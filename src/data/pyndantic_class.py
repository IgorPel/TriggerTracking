# --- МОДЕЛІ ДАНИХ ---
from pydantic import BaseModel
from typing import List

class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str | None = None


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    password: str

class AddTrigger(BaseModel):
    function: str
    arguments: str

class PortfolioItemCreate(BaseModel):
    currency_symbol: str
    amount: float
    buy_price: float

class PortfolioResponse(BaseModel):
    currency: str
    amount: float
    current_price: float | None
    total_value: float | None
    profit_loss: float | None


class QueueItem(BaseModel):
    operation: str
    arg1: str
    arg2: str
    boolean_operation: str | None


class QueueRequest(BaseModel):
    items: List[QueueItem]

