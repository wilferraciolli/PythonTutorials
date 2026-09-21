from fastapi import FastAPI

from routers import health, users, tags, todos

app = FastAPI(title="TODO API", version="1.0.0", description="Portable FastAPI TODO API")

app.include_router(health.router)
app.include_router(users.router)
app.include_router(tags.router)
app.include_router(todos.router)
