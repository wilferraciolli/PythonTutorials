from fastapi import FastAPI
from routers import health, todos

app = FastAPI(title="TODO api", version="1.0.0")

# REgister routers
app.include_router(health.router)
app.include_router(todos.router)

