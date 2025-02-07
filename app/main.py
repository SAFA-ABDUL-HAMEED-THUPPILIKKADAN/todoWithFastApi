from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn
from . import models, schemas, database, token
from sqlalchemy.orm import Session
from .database import engine
from fastapi.responses import JSONResponse
from .hashing import Hash
from . import oauth2
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    # Allow all origins (for development; restrict in production)
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)


models.Base.metadata.create_all(engine)


@app.get('/')
def unpublished():
    return 'hello-world'


@app.post('/signup')
def create_user(request: schemas.User, db: Session = Depends(database.get_db)):
    # Check if the email already exists
    existing_user = db.query(models.User).filter(
        models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    new_user = models.User(
        name=request.name,
        email=request.email,
        password=Hash.bcrypt(request.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user": new_user}


@app.post('/login')
def login(request: schemas.ShowUser, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(
        models.User.email == request.email).first()
    if not user:
        return JSONResponse(
            status_code=404,  # Bad Request
            content={"email": "Invalid."}
        )
    if not Hash.verify(user.password, request.password):
        return JSONResponse(
            status_code=404,  # Bad Request
            content={"password": "Invalid."}
        )
    access_token = token.create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/create", status_code=status.HTTP_201_CREATED)
def createTodo(request: schemas.Todo, db: Session = Depends(database.get_db), current_user: schemas.TokenData = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(
        models.User.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_todo = models.Todo(
        title=request.title,
        deadline=request.deadline,
        isCompleted=False,
        creator_id=user.id
    )

    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)  # Refresh to get the generated ID

    return new_todo  # Return the newly created todo


@app.get('/getAll', response_model=List[schemas.Todo])
def all(db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(
        models.User.email == current_user.email).first()
    todos = db.query(models.Todo).filter(
        models.Todo.creator_id == user.id).all()
    return todos


@app.get('/getAll/{id}', status_code=200, response_model=schemas.Todo)
def show(id: int, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    todo = db.query(models.Todo).filter(models.Todo.id == id).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Todo with the id {id} is not available")

    return todo


@app.delete('/delete/{id}', status_code=status.HTTP_204_NO_CONTENT)
def destroy(id: int, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(
        models.User.email == current_user.email).first()
    todo = db.query(models.Todo).filter(models.Todo.id == id,
                                        models.Todo.creator_id == user.id)

    if not todo.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Todo with id {id} not found")

    todo.delete(synchronize_session=False)
    db.commit()

    return {"message": "Todo deleted successfully"}


@app.put("/update/{id}", status_code=status.HTTP_202_ACCEPTED)
def update(id: int, request: schemas.TodoUpdate, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(
        models.User.email == current_user.email).first()
    todo = db.query(models.Todo).filter(models.Todo.id == id,
                                        models.Todo.creator_id == user.id).first()

    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Todo with id {id} is not found")

    if request.isCompleted is not None:
        todo.isCompleted = request.isCompleted
        todo.completedAt = datetime.utcnow() if request.isCompleted else None

    if request.title:
        todo.title = request.title
    if request.deadline:
        todo.deadline = request.deadline

    db.commit()
    db.refresh(todo)
    return todo
