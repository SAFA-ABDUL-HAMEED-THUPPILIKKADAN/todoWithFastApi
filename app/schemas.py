
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    name: str
    email: str
    password: str


class ShowUser(BaseModel):
    email: str
    password: str

    class Config():
        orm_mode = True


class Todo(BaseModel):
    title: str
    deadline: datetime
    isCompleted: bool


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    deadline: Optional[datetime] = None
    isCompleted: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
