from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import List
from models import Todo, TodoCreate, TodoState

app = FastAPI(title="TODO api", version="1.0.0")


# in memory database (hasmap)
todos_db: dict[int, dict] = {}
next_id = 1

# CREATE
@app.post("/todos", response_model=Todo)
def create_todo(todo: TodoCreate):
    """Create a new todo"""
    global next_id

    new_todo = {
        "id": next_id,
        "title": todo.title,
        "description": todo.description,
        "complete_by": todo.complete_by,
        "state": TodoState.NEW,
        "created_at": datetime.now()
    }

    todos_db[next_id] = new_todo
    next_id += 1

    return new_todo


# GET ALL
@app.get("/todos", response_model=List[Todo])
def get_all_todos(state: TodoState = None):
    """Get all TODOs, optionally filtered by state"""
    todos = list(todos_db.values())

    if state:
        todos = [t for t in todos if t["state"] == state]

    return todos


# READ ONE - GET
@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    """Get a single TODO by ID"""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="TODO not found")

    return todos_db[todo_id]


# UPDATE - PUT
@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoCreate):
    """Update a TODO"""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="TODO not found")

    todos_db[todo_id].update({
        "title": todo_update.title,
        "description": todo_update.description,
        "complete_by": todo_update.complete_by
    })

    return todos_db[todo_id]


# UPDATE STATE - PATCH (like a partial update)
@app.patch("/todos/{todo_id}/state/{new_state}")
def update_todo_state(todo_id: int, new_state: TodoState):
    """Update only the state of a TODO"""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="TODO not found")

    todos_db[todo_id]["state"] = new_state

    return todos_db[todo_id]


# DELETE - DELETE
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    """Delete a TODO"""
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="TODO not found")

    deleted = todos_db.pop(todo_id)

    return {"message": "TODO deleted", "deleted_todo": deleted}


# Health check
@app.get("/health")
def health_check():
    return {"status": "API is running"}
