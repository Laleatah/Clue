import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, File, UploadFile, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc, or_
from app.database import get_db
from app.models import Post, Comment, User
from app.schemas import PostCreate, PostUpdate, PostResponse, CommentCreate, CommentResponse, PaginatedPosts
from app.deps import get_current_user

router = APIRouter(prefix="/api/posts", tags=["Posts & Comments"])

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("Общее"),
    status: str = Form("active"),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_url = None
    if image and image.filename:
        UPLOAD_DIR = "static/uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{image.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/{file_path}"

    new_post = Post(
        title=title, content=content, owner_id=current_user.id,
        category=category, status=status, image_url=image_url
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("", response_model=PaginatedPosts)
def get_posts(
    search: str = "", 
    category: str = "",
    sort: str = "created_at_desc",
    limit: int = 5, 
    offset: int = 0, 
    db: Session = Depends(get_db)
):
    # Базовый запрос (SQLAlchemy 2.0)
    query = select(Post).where(Post.is_published == True)
    
    # Поиск
    if search:
        query = query.where(Post.title.ilike(f"%{search}%"))
    
    # Фильтр
    if category:
        query = query.where(Post.category == category)
        
    # Сортировка
    if sort == "created_at_desc":
        query = query.order_by(desc(Post.created_at))
    elif sort == "created_at_asc":
        query = query.order_by(asc(Post.created_at))
    elif sort == "title_asc":
        query = query.order_by(asc(Post.title))
        
    # Считаем общее количество для пагинации (с учетом фильтров)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    
    # Пагинация
    posts = db.scalars(query.offset(offset).limit(limit)).all()
    
    return {"items": posts, "total": total}

@router.get("/stats")
def get_posts_stats(db: Session = Depends(get_db)):
    # Требование ТЗ п.3.3: Статистика с group_by
    stmt = select(Post.category, func.count(Post.id)).group_by(Post.category)
    results = db.execute(stmt).all()
    
    stats = {category: count for category, count in results}
    total_count = db.scalar(select(func.count(Post.id)))
    
    return {"total_count": total_count, "by_category": stats}

@router.get("/{id}", response_model=PostResponse)
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.scalar(select(Post).where(Post.id == id))
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    post.views_count += 1
    db.commit()
    db.refresh(post)
    return post

@router.patch("/{id}", response_model=PostResponse)
def update_post(id: int, post_data: PostUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.scalar(select(Post).where(Post.id == id))
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только автор может редактировать")
        
    # exclude_unset=True позволяет обновлять только переданные поля
    update_data = post_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
        
    db.commit()
    db.refresh(post)
    return post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.scalar(select(Post).where(Post.id == id))
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Только автор может удалять")
        
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(id: int, comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.scalar(select(Post).where(Post.id == id))
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
        
    new_comment = Comment(text=comment_data.text, post_id=id, owner_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment