from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # Берем user_id из сессии (SessionMiddleware)
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")
    
    # SQLAlchemy 2.0 стиль
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
        
    return user