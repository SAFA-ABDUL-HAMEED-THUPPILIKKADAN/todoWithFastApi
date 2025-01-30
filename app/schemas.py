
from pydantic import BaseModel
from datetime import date


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
    deadline: date
    isCompleted: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
