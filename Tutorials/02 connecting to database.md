Let me create a plan for integrating SQLite with **SQLAlchemy** (Python's ORM, like Hibernate/JPA in Java).



## 📋 What We'll Do


Plain text






```
fastapi-learning/
├── main.py
├── models.py              # Pydantic models (API contracts)
├── database.py            # NEW - SQLAlchemy setup
├── db_models.py           # NEW - SQLAlchemy models (ORM)
├── utils.py
├── routers/
│   ├── health.py
│   └── todos.py           # Updated to use database
├── todo.db                # NEW - SQLite database file
└── venv/

```






## 🔄 Java Comparison




































| Java | Python |
| --- | --- |
| Hibernate/JPA | SQLAlchemy |
| `@Entity` class | SQLAlchemy `Base` model |
| `@Column` | SQLAlchemy `Column` |
| `SessionFactory` | SQLAlchemy `engine` |
| `Session` | SQLAlchemy `Session` |
| `DAO` / `Repository` | Direct queries in endpoints |




## ✅ Step 1: Install Dependencies


Bash






```
pip install sqlalchemy
pip freeze > requirements.txt

```






## 📝 Step 2: Create `database.py`


This sets up SQLite connection:


Python






```
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Create SQLite database file (local)
DATABASE_URL = "sqlite:///./todo.db"

# Create engine (connection pool)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Dependency function for FastAPI
def get_db():
    """Dependency to inject database session into endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

```






## 🗂️ Step 3: Create `db_models.py`


Database models (like `@Entity` in Java):


Python






```
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

```






## 🔧 Step 4: Update `main.py`


Add database initialization:


Python






```
from fastapi import FastAPI
from database import engine, Base
from routers import health, todos

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TODO API", version="1.0.0")

app.include_router(health.router)
app.include_router(todos.router)

```






## 🚀 Step 5: Update `routers/todos.py`


Replace in-memory dict with database queries:


Python






```
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from models import Todo, TodoCreate, TodoUpdate, TodoState
from db_models import TodoDB
from database import get_db
from utils import TodoUtils

router = APIRouter(prefix="/todos", tags=["todos"])

# CREATE - POST
@router.post("", response_model=Todo, status_code=201)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)) -> Todo:
    """Create a new TODO"""
    db_todo = TodoDB(
        title=todo.title,
        description=todo.description,
        complete_by=todo.complete_by,
        state=todo.state,
        created_date=datetime.now()
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

# READ ALL - GET
@router.get("", response_model=List[Todo])
def get_all_todos(state: Optional[TodoState] = None, db: Session = Depends(get_db)) -> List[Todo]:
    """Get all TODOs, optionally filtered by state"""
    query = db.query(TodoDB)
    
    if state:
        query = query.filter(TodoDB.state == state)
    
    return query.all()

# READ ONE - GET
@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, db: Session = Depends(get_db)) -> Todo:
    """Get a single TODO by ID"""
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    
    if not db_todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    todo = Todo.from_orm(db_todo)
    
    if TodoUtils.is_overdue(todo):
        print(f"⚠️ TODO {todo_id} is overdue!")
    
    if TodoUtils.is_due_soon(todo, days=3):
        print(f"⏰ TODO {todo_id} is due soon!")
    
    return db_todo

# UPDATE - PUT
@router.put("/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)) -> Todo:
    """Update a TODO (partial update)"""
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    
    if not db_todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    # Only update fields that were provided
    update_data = todo_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_todo, key, value)
    
    db.commit()
    db.refresh(db_todo)
    return db_todo

# UPDATE STATE - PATCH
@router.patch("/{todo_id}/state/{new_state}", response_model=Todo)
def update_todo_state(todo_id: int, new_state: TodoState, db: Session = Depends(get_db)) -> Todo:
    """Update only the state of a TODO"""
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    
    if not db_todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    db_todo.state = new_state
    db.commit()
    db.refresh(db_todo)
    return db_todo

# DELETE - DELETE
@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a TODO"""
    db_todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    
    if not db_todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    db.delete(db_todo)
    db.commit()

```






## 🎯 Key Concepts (Java → Python)








































| Java | Python |
| --- | --- |
| `@Entity public class Todo` | `class TodoDB(Base)` |
| `@Column String title` | `title = Column(String(80))` |
| `SessionFactory` | `engine` |
| `@Autowired private Session db` | `db: Session = Depends(get_db)` |
| `db.save(todo)` | `db.add(todo); db.commit()` |
| `db.findById(id)` | `db.query(TodoDB).filter(...).first()` |
| `db.delete(todo)` | `db.delete(todo); db.commit()` |




## ✅ Ready?


Create these 4 files in order:



1. `database.py`

2. `db_models.py`

3. Update `main.py`

4. Update `routers/todos.py`



Then run:


Bash






```
uvicorn main:app --reload

```





A `todo.db` file will be created automatically! 🚀


Let me know when you're ready or if you hit any issues!