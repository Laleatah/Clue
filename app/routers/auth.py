from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, UserResponse
from app.security import hash_password, verify_password
from app.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(User.username == user_data.username))
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    new_user = User(
        username=user_data.username, 
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == user_data.username))
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    # Сохраняем user_id в сессию (SessionMiddleware подпишет куку)
    request.session["user_id"] = user.id
    return {"message": "Успешный вход", "username": user.username}

@router.post("/logout")
def logout(request: Request):
    request.session.clear() # Очищаем сессию
    return {"message": "Успешный выход"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    # Требование ТЗ п.3.1
    return current_user