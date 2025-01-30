from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from .database import Base
from datetime import date
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'signupuser'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)

    todos = relationship('Todo', back_populates='creator')


class Todo(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    deadline = Column(Date, nullable=False)
    createdAt = Column(Date, nullable=False, default=date.today)
    isCompleted = Column(Boolean, nullable=False, default=True)
    creator_id = Column(Integer, ForeignKey('signupuser.id'))

    creator = relationship("User", back_populates="todos")
