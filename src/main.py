from contextlib import asynccontextmanager  # <--- Треба для подій старту

from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles

from src.data.database import engine, Base
from src.endpoints import router as endpoints_router

import asyncio

# --- LIFESPAN (Створення таблиць при старті) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Цей код виконається при запуску сервера
    await asyncio.sleep(3)

    async with engine.begin() as conn:
        # Створюємо таблиці, якщо їх немає
        await conn.run_sync(Base.metadata.create_all)
    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.include_router(endpoints_router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
