from fastapi import Depends, FastAPI

from auth import get_authenticated_user
from routers import health, me, tags, todos, user_profile, users

app = FastAPI(
    title="TODO API",
    version="1.0.0",
    description="Portable FastAPI TODO API",
)

app.include_router(health.router)
app.include_router(me.router, dependencies=[Depends(get_authenticated_user)])
app.include_router(user_profile.router, dependencies=[Depends(get_authenticated_user)])
app.include_router(users.router, dependencies=[Depends(get_authenticated_user)])
app.include_router(tags.router, dependencies=[Depends(get_authenticated_user)])
app.include_router(todos.router, dependencies=[Depends(get_authenticated_user)])
