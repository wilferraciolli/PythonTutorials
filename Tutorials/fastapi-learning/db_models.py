from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
from database import Base
from models import TodoState


class TodoDB(Base):
    """SQLAlchemy TODO model (maps to database table)"""
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(80), nullable=False)
    description = Column(String, nullable=True)
    complete_by = Column(DateTime, nullable=False)
    state = Column(Enum(TodoState), default=TodoState.NEW, nullable=False)
    created_date = Column(DateTime, default=datetime.now, nullable=False)
