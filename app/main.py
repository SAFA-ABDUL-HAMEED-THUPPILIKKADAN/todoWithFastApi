from fastapi import FastAPI, Depends
import uvicorn
from . import models, schemas, database
from sqlalchemy.orm import Session
from .database import engine

app = FastAPI()

models.Base.metadata.create_all(engine)


@app.get('/')
def unpublished():
    return 'hello-world'


@app.post('/signup')
def create(request: schemas.User, db: Session = Depends(database.get_db)):
    new_user = models.User(
        name=request.name, email=request.email, password=request.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
