from sqlalchemy.orm import Session
from typing import List, Optional

from db_models import TodoDB
from models import TodoState


class TodoRepository:
    """Repository for TODO database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(
            self,
            title: str,
            description: optional[str],
            complete_by,
            state: TodoState) -> TodoDB:
        """Create a new TODO in database"""
        db_todo = TodoDB(
            title=title,
            description=description,
            complete_by=complete_by,
            state=state
        )
        self.db.add(db_todo)
        self.db.commit()
        self.db.refresh(db_todo)

        return db_todo

    def get_by_id(self, todo_id: int) -> Optional[TodoDB]:
        """Get TODO by ID"""
        return (self.db.query(TodoDB)
                .filter(TodoDB.id == todo_id)
                .first())

    def get_all(self, state: Optional[TodoState] = None) -> List[TodoDB]:
        """Get all TODOs, optionally filtered by state"""
        query = self.db.query(TodoDB)

        if state:
            query = query.filter(TodoDB.state == state)

        return (query
                .all())

    def update(self, todo_id: int, **kwargs) -> Optional[TodoDB]:
        """Update TODO fields"""
        db_todo = self.get_by_id(todo_id)

        if not db_todo:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(db_todo, key, value)

        self.db.commit()
        self.db.refresh(db_todo)

        return db_todo

    def delete(self, todo_id: int) -> bool:
        """Delete TODO"""
        db_todo = self.get_by_id(todo_id)

        if not db_todo:
            return False

        self.db.delete(db_todo)
        self.db.commit()

        return True