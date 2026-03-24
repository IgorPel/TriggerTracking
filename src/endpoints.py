from fastapi import APIRouter, Request, Depends, HTTPException, Response, status, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from src.data.pyndantic_class import UserCreate, Token, User, QueueRequest
from src.data.database import get_db, UserDB, Triggers, UserToTriggers
from src.utilities import pwd_context, verify_password, create_access_token, get_current_user_from_cookie, prepare_trigger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, text, insert, func, and_, ColumnElement

from starlette.websockets import WebSocket
from starlette.responses import HTMLResponse

import redis.asyncio as redis
import asyncio
from datetime import timedelta
from typing import cast
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")


templates = Jinja2Templates(directory="src/templates")

router = APIRouter()

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", status_code=201)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Перевірка чи існує
    result = await db.execute(
                    select(UserDB)
                    .where(
                        UserDB.nickname == user_data.username
                    )
            )
    user = result.scalar_one_or_none()
    if user is not None:
        raise HTTPException(status_code=400, detail="User already exists")

    # Хешування пароля
    hashed_password_res = pwd_context.hash(user_data.password)
    new_user = UserDB(
        nickname=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password_res,
    )

    db.add(new_user)
    await db.commit()  # <--- ВАЖЛИВО! Зберігаємо зміни
    await db.refresh(new_user)  # <--- Оновлюємо об'єкт (отримуємо ID)

    return {"message": "User created successfully"}

@router.get('/login', response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_model=Token)
async def login_for_access_token(response: Response,
                                 form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: AsyncSession = Depends(get_db)):
    result = await db.execute(
                    select(UserDB)
                    .where(
                        UserDB.nickname == form_data.username
                    )
            )
    user = result.scalar_one_or_none()

    # ВИПРАВЛЕНО: Звертаємось через крапку user.hashed_password, а не ["..."]
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    # ВИПРАВЛЕНО: user.nickname
    access_token = create_access_token(
        data={"sub": user.nickname}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/tracking/", response_class=HTMLResponse)
async def tracking(request: Request,
                   db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(get_current_user_from_cookie)):
    id = current_user.id
    sql = text("""
       SELECT 
            t.id as trigger_id,
            ut.is_active,
            ut.last_triggered,
            STRING_AGG(
                UPPER(elem->>'arg1'), ', ') as currency,
            STRING_AGG(
                CONCAT(UPPER(elem->>'arg1'), ' ', elem->>'operation', ' ', elem->>'arg2', '$ ', elem->>'boolean_operation'),
                ' '
            ) as pretty_condition
        FROM triggers t
        JOIN "UserToTriggers" ut ON t.id = ut.trigger_id
        CROSS JOIN jsonb_array_elements(t.func) as elem
        WHERE ut.user_id = :uid
        GROUP BY t.id, ut.is_active, ut.last_triggered
        ORDER BY t.id ASC
    """)

    result = await db.execute(sql, {"uid": id})
    triggers_data = result.all()

    return templates.TemplateResponse(
        request=request,
        name="tracking.html",
        context={"user_id": current_user.id,
                 "use-rname": current_user.nickname,
                 "triggers": triggers_data})

@router.get("/add_trigger", response_class=HTMLResponse)
async def add_trigger(request: Request):
    return templates.TemplateResponse("add_trigger.html", {"request": request})

@router.post("/add_trigger")
async def add_trigger(trigger: QueueRequest,
                      db: AsyncSession = Depends(get_db),
                      current_user: UserDB = Depends(get_current_user_from_cookie)):
    content_hash, list_trigger = await prepare_trigger(trigger)

    result = await db.execute(
        select(Triggers)
        .where(
            Triggers.content_hash == content_hash
        )
    )

    triggerDB = result.scalar_one_or_none()

    # подивись чи є той зв'язок.

    if triggerDB is not None:

        result = await db.execute(
                    select(UserToTriggers).where(
                        and_(
                            UserToTriggers.c.user_id == current_user.id,
                            UserToTriggers.c.trigger_id == triggerDB.id)
                    )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(status_code=404, detail="Trigger not found")

        command = insert(UserToTriggers).values(user_id=current_user.id, trigger_id=triggerDB.id)
        await db.execute(command)
    else:
        await db.refresh(current_user, ["triggers"])
        new_trigger = Triggers(func=list_trigger, content_hash=content_hash)
        current_user.triggers.append(new_trigger)
        db.add(new_trigger)
    await db.commit()
    return {"message": "Trigger added successfully"}


@router.get("/edit/{trigger_id}", response_class=HTMLResponse)
async def edit_trigger(request: Request,
                       trigger_id: int,
                       db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user_from_cookie)):
    result = await db.execute(
                select(UserToTriggers).where(
                    and_(
                        UserToTriggers.c.user_id == user.id,
                        UserToTriggers.c.trigger_id == trigger_id
                    )
                )
            )

    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="You didn't have that trigger")

    result = await db.execute(select(Triggers).where(Triggers.id == trigger_id))
    trigger = result.scalar_one_or_none()
    if trigger is None:
        raise HTTPException(status_code=404, detail="Trigger not found NEW!!")
    else:
        return templates.TemplateResponse("add_trigger.html",
                                      {"request": request,
                                       "trigger_id": trigger_id,
                                       "trigger_data": trigger.func})



@router.put("/edit/{trigger_id}")
async def edit_trigger(trigger_id: int,
                       trigger: QueueRequest,
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user_from_cookie)):

    content_hash, list_trigger = await prepare_trigger(trigger)


    #дивимося чи є ще такий тригер.
    result = await db.execute(
                    select(Triggers)
                    .where(
                            Triggers.content_hash == content_hash
                    )
            )

    triggerFrDB = result.scalar_one_or_none()

    result = await db.execute(
                    select(UserToTriggers).where(
                        and_(
                            UserToTriggers.c.user_id == current_user.id,
                            UserToTriggers.c.trigger_id == triggerFrDB.id
                        )
                    )
    )

    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="You already have this trigger")

    # глянь чи буде ще такий.
    if triggerFrDB is not None:

        result = await db.execute(
                    select(UserToTriggers.c.is_active)
                    .where(
                        cast(ColumnElement, UserToTriggers.c.trigger_id == triggerFrDB.id)
                    )
                )

        await db.execute(
            update(UserToTriggers).where(
                and_(
                    UserToTriggers.c.user_id == current_user.id,
                    UserToTriggers.c.trigger_id == trigger_id
                )
            )
            .values(
                trigger_id=triggerFrDB.id,
                is_active=result.scalar_one_or_none()
            )
        )


        result = await db.execute(
            select(
                func.count(UserToTriggers.c.trigger_id)
            )
            .where(
                cast(ColumnElement, UserToTriggers.c.trigger_id == trigger_id)
            )
        )

        if result.scalar_one_or_none() is None:
            await db.execute(
                delete(Triggers)
                .where(
                    Triggers.id == trigger_id
                )
            )
    else:
        # дивимося чи є хтось ще підписанний на цей тригер.
        result = await db.execute(
                select(
                    func.count(UserToTriggers.c.user_id)
                )
                .where(
                    cast(ColumnElement, UserToTriggers.c.trigger_id == trigger_id)
                )
            )


        if result.scalar_one_or_none() != 1:
            new_trigger = Triggers(func=list_trigger, content_hash=content_hash)
            db.add(new_trigger)
            await db.commit()
            await db.refresh(new_trigger)
            await db.execute(
                update(UserToTriggers).where(
                    and_(
                        UserToTriggers.c.user_id == current_user.id,
                        UserToTriggers.c.trigger_id == trigger_id
                    )
                )
                .values(
                    trigger_id=new_trigger.id,
                    is_active=False
                )
            )

            # а куди зв'язок ?
        else:
            await db.execute(
                update(Triggers)
                .where(
                    Triggers.id == trigger_id
                )
                .values(
                    content_hash=content_hash,
                    func=list_trigger
                )
            )
    await db.commit()

@router.delete("/delete/{trigger_id}")
async def delete_trigger(trigger_id: int,
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user_from_cookie)):
    await db.execute(
        delete(UserToTriggers).where(
        and_(
            UserToTriggers.c.user_id == current_user.id,
            UserToTriggers.c.trigger_id == trigger_id
        )
    ))

    result = await db.execute(
        select(UserToTriggers)
        .where(
            UserToTriggers.c.trigger_id == trigger_id
        )
    )
    if result.scalar_one_or_none() is None:
        await db.execute(
            delete(Triggers)
            .where(
                Triggers.id == trigger_id
            )
        )
    await db.commit()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    print(f"{user_id} connected")
    r = redis.from_url(REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()

    channel = f"alerts-{user_id}"
    await pubsub.subscribe(channel)
    try:
        # Нескінченний цикл слухання
        while True:
            # Чекаємо повідомлення з Redis
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            if message:
                # Якщо прийшло повідомлення з Redis -> шлемо в WebSocket
                data = message["data"]
                await websocket.send_text(data)

            # Важливо: даємо час іншим процесам (heartbeat), щоб з'єднання не розірвалося
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Закриваємо з'єднання
        await pubsub.unsubscribe(channel)
        await r.close()


