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
    print(current_user.email)
    new_todo = models.Todo(
        title=request.title, deadline=request.deadline, isCompleted=request.isCompleted,  creator_id=user.id)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)

    return new_todo


@app.get('/getAll', response_model=schemas.Todo)
def all(db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(
        models.User.email == current_user.email).first()
    todos = db.query(models.Todo).filter(
        models.Todo.creator_id == user.id).first()
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
    todo = db.query(models.Todo).filter(models.Todo.id == id)
    if not todo.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} is not found")
    todo.delete(synchronize_session=False)
    db.commit()
    return "deleted"


@app.put('/update/{id}', status_code=status.HTTP_202_ACCEPTED)
def update(id: int, request: schemas.Todo, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    update_data = request.model_dump(exclude_unset=True)
    todo = db.query(models.Todo).filter(models.Todo.id == id)
    if not todo.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} is not found")
    todo.update(update_data)
    db.commit()
    return "updated successfully"
