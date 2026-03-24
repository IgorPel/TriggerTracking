import os
from os import getenv

from fastapi import Depends, HTTPException, status
from fastapi import Cookie

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.data.database import get_db, UserDB
from src.data.pyndantic_class import QueueRequest

from typing import Any
import json
import hashlib
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext


load_dotenv()



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_logic_hash(payload: Any) -> str:

    def normalize(data):
        if isinstance(data, list):
            return [normalize(item) for item in data]
        if isinstance(data, dict):
            # Сортуємо ключі та чистимо значення
            return {k: normalize(v) for k, v in data.items()}
        # Перетворюємо все в string і прибираємо пробіли по боках
        return str(data).strip()

    clean_payload = normalize(payload)

    # Робимо дамп
    json_str = json.dumps(clean_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, getenv("SECRET_KEY", "super_secret_key_change_me_please"),
                             algorithm=os.getenv("ALGORITHM", "HS256"))
    return encoded_jwt

async def get_current_user_from_cookie(
        access_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db)):

    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = access_token.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, getenv("SECRET_KEY", "super_secret_key_change_me_please"),
                             algorithms=[os.getenv("ALGORITHM", "HS256")])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

    except jwt.InvalidTokenError:
        raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

    query = select(UserDB).where(UserDB.nickname == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
    return user

async def prepare_trigger(trigger: QueueRequest):
    list_trigger = []
    i = 0
    for part in trigger.items:
        dict_part = part.model_dump()
        dict_part["arg1"] = dict_part["arg1"].strip().lower().replace(" ", "-")
        if dict_part["arg1"] == "usdc":
            dict_part["arg1"] = "usdc-coin"
        dict_part["part_id"] = i
        list_trigger.append(dict_part)
        i -= -1

    content_hash = generate_logic_hash(list_trigger)

    return content_hash, list_trigger

