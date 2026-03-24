from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Float, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.pool import NullPool


from dotenv import load_dotenv
import os
load_dotenv()

engine = create_async_engine(os.getenv("DATABASE_URL"), echo=True, poolclass=NullPool,)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass

from sqlalchemy import Table, Column, ForeignKey, String

UserToTriggers = Table(
    "UserToTriggers",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("trigger_id", ForeignKey("triggers.id"), primary_key=True),
    Column("is_active", Boolean, default=False),
    Column("last_triggered", TIMESTAMP(timezone=True)),
)



class UserDB(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    triggers: Mapped[list["Triggers"]] = relationship(
        secondary=UserToTriggers,
        back_populates="users",
    )


class Triggers(Base):
    __tablename__ = 'triggers'
    id: Mapped[int] = mapped_column(primary_key=True)
    func: Mapped[dict] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    users: Mapped[list["UserDB"]] = relationship(
        secondary=UserToTriggers,
        back_populates="triggers",
    )

class PortfolioItemDB(Base):
    __tablename__ = 'portfolio_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    currency_symbol: Mapped[str] = mapped_column(String(20)) # "bitcoin"
    amount: Mapped[float] = mapped_column(Float)             # 0.5
    buy_price: Mapped[float] = mapped_column(Float)          # 50000.0


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
