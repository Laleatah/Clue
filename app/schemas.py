from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# --- Пользователи ---
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

# --- Посты ---
class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    category: str = "Общее"
    status: str = "active"

class PostUpdate(BaseModel): # Для PATCH запроса
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    is_published: Optional[bool] = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    is_published: bool
    views_count: int
    owner_id: int
    category: str
    status: str
    image_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Схема для пагинации (чтобы фронт получил items и total)
class PaginatedPosts(BaseModel):
    items: List[PostResponse]
    total: int

# --- Комментаии ---
class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)

class CommentResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    post_id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)