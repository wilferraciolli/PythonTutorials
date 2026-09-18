from fastapi import FastAPI
from routers import health, todos
from database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TODO api", version="1.0.0")

# Register routers
app.include_router(health.router)
app.include_router(todos.router)

