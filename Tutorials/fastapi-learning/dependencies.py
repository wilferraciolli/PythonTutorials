from sqlalchemy.orm import Session
from database import SessionLocal
from fastapi import Depends

from repositories.todo_repository import TodoRepository
from services.todo_service import TodoService

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_todo_repository(db: Session = Depends(get_db)) -> TodoRepository:
    """Inject TodoRepository - depends on db session"""
    return TodoRepository(db)

def get_todo_service(repository: TodoRepository = Depends(get_todo_repository)) -> TodoService:
    """Inject TodoService - depends on repository"""
    return TodoService(repository)
