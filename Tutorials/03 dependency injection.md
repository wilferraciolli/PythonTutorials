Excellent! That's **proper architecture** - exactly like Java with Spring! Let me create:



1. **Repository** - Database queries (DAO pattern)

2. **Service** - Business logic

3. **Dependencies** - DI container

4. **Routers** - Just call the service




## 📁 Project Structure


Plain text






```
fastapi-learning/
├── main.py
├── models.py
├── database.py
├── db_models.py
├── utils.py
├── dependencies.py         # NEW - DI setup
├── repositories/           # NEW folder
│   ├── __init__.py
│   └── todo_repository.py  # NEW - Database access
├── services/               # NEW folder
│   ├── __init__.py
│   └── todo_service.py     # NEW - Business logic
├── routers/
│   ├── health.py
│   └── todos.py            # Updated - use service
└── venv/

```






## 🏗️ Step 1: Create `repositories/todo_repository.py`


Database access layer (like Java DAO):


Python






```
from sqlalchemy.orm import Session
from typing import List, Optional
from db_models import TodoDB
from models import TodoState

class TodoRepository:
    """Repository for TODO database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, title: str, description: Optional[str], 
               complete_by, state: TodoState) -> TodoDB:
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
        return self.db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    
    def get_all(self, state: Optional[TodoState] = None) -> List[TodoDB]:
        """Get all TODOs, optionally filtered by state"""
        query = self.db.query(TodoDB)
        
        if state:
            query = query.filter(TodoDB.state == state)
        
        return query.all()
    
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

```






## 💼 Step 2: Create `services/todo_service.py`


Business logic layer:


Python






```
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from models import Todo, TodoCreate, TodoUpdate, TodoState
from repositories.todo_repository import TodoRepository
from utils import TodoUtils

class TodoService:
    """Service for TODO business logic"""
    
    def __init__(self, repository: TodoRepository):
        self.repository = repository
    
    def create_todo(self, todo_create: TodoCreate) -> Todo:
        """Create a new TODO"""
        db_todo = self.repository.create(
            title=todo_create.title,
            description=todo_create.description,
            complete_by=todo_create.complete_by,
            state=todo_create.state
        )
        return Todo.from_orm(db_todo)
    
    def get_todo(self, todo_id: int) -> Optional[Todo]:
        """Get TODO by ID"""
        db_todo = self.repository.get_by_id(todo_id)
        
        if not db_todo:
            return None
        
        todo = Todo.from_orm(db_todo)
        
        # Check status
        if TodoUtils.is_overdue(todo):
            print(f"⚠️ TODO {todo_id} is overdue!")
        
        if TodoUtils.is_due_soon(todo, days=3):
            print(f"⏰ TODO {todo_id} is due soon!")
        
        return todo
    
    def get_all_todos(self, state: Optional[TodoState] = None) -> List[Todo]:
        """Get all TODOs"""
        db_todos = self.repository.get_all(state=state)
        return [Todo.from_orm(todo) for todo in db_todos]
    
    def update_todo(self, todo_id: int, todo_update: TodoUpdate) -> Optional[Todo]:
        """Update TODO"""
        update_data = todo_update.dict(exclude_unset=True)
        
        db_todo = self.repository.update(todo_id, **update_data)
        
        if not db_todo:
            return None
        
        return Todo.from_orm(db_todo)
    
    def update_todo_state(self, todo_id: int, new_state: TodoState) -> Optional[Todo]:
        """Update TODO state only"""
        db_todo = self.repository.update(todo_id, state=new_state)
        
        if not db_todo:
            return None
        
        return Todo.from_orm(db_todo)
    
    def delete_todo(self, todo_id: int) -> bool:
        """Delete TODO"""
        return self.repository.delete(todo_id)

```






## 🔗 Step 3: Create `dependencies.py`


Dependency injection setup (like Spring's @Configuration):


Python






```
from sqlalchemy.orm import Session
from database import SessionLocal
from repositories.todo_repository import TodoRepository
from services.todo_service import TodoService

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_todo_repository(db: Session = None) -> TodoRepository:
    """Inject TodoRepository"""
    if db is None:
        db = SessionLocal()
    return TodoRepository(db)

def get_todo_service(repository: TodoRepository = None) -> TodoService:
    """Inject TodoService"""
    if repository is None:
        repository = get_todo_repository()
    return TodoService(repository)

```






## 🚀 Step 4: Create `repositories/__init__.py` and `services/__init__.py`


Just empty files (makes them packages):


Python






```
# Both files can be empty

```






## 📝 Step 5: Update `routers/todos.py`


Now it's **clean and simple** - just calls the service:


Python






```
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from models import Todo, TodoCreate, TodoUpdate, TodoState
from services.todo_service import TodoService
from dependencies import get_todo_service

router = APIRouter(prefix="/todos", tags=["todos"])

# CREATE - POST
@router.post("", response_model=Todo, status_code=201)
def create_todo(todo: TodoCreate, service: TodoService = Depends(get_todo_service)) -> Todo:
    """Create a new TODO"""
    return service.create_todo(todo)

# READ ALL - GET
@router.get("", response_model=List[Todo])
def get_all_todos(
    state: Optional[TodoState] = None,
    service: TodoService = Depends(get_todo_service)
) -> List[Todo]:
    """Get all TODOs"""
    return service.get_all_todos(state=state)

# READ ONE - GET
@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, service: TodoService = Depends(get_todo_service)) -> Todo:
    """Get a single TODO by ID"""
    todo = service.get_todo(todo_id)
    
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    return todo

# UPDATE - PUT
@router.put("/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    service: TodoService = Depends(get_todo_service)
) -> Todo:
    """Update a TODO"""
    todo = service.update_todo(todo_id, todo_update)
    
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    return todo

# UPDATE STATE - PATCH
@router.patch("/{todo_id}/state/{new_state}", response_model=Todo)
def update_todo_state(
    todo_id: int,
    new_state: TodoState,
    service: TodoService = Depends(get_todo_service)
) -> Todo:
    """Update TODO state"""
    todo = service.update_todo_state(todo_id, new_state)
    
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    
    return todo

# DELETE - DELETE
@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, service: TodoService = Depends(get_todo_service)) -> None:
    """Delete a TODO"""
    success = service.delete_todo(todo_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")

```






## 🎯 Architecture Overview


Plain text






```
Endpoint (Router)
    ↓ (calls)
Service (Business Logic)
    ↓ (calls)
Repository (Database)
    ↓ (calls)
Database (SQLite)

```






## 🔄 Java Comparison




























| Java | Python |
| --- | --- |
| `@Repository interface TodoDAO` | `class TodoRepository` |
| `@Service class TodoService` | `class TodoService` |
| `@Configuration class DependencyConfig` | `dependencies.py` |
| `@Autowired private TodoService service` | `service: TodoService = Depends(get_todo_service)` |




## ✅ Ready?


Create these files in order:



1. `repositories/__init__.py` (empty)

2. `services/__init__.py` (empty)

3. `repositories/todo_repository.py`

4. `services/todo_service.py`

5. `dependencies.py`

6. Update `routers/todos.py`

7. Update `main.py` to use database



Then test! 🚀