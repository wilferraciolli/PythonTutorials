from fastapi import Depends, FastAPI

from auth import get_authenticated_user
from cors import EnvCORSMiddleware
from errors import register_error_handlers
from routers import (
    admin,
    assistant,
    chats,
    engagement_analytics,
    groups,
    health,
    me,
    media,
    post_comments,
    posts,
    tags,
    timeline,
    todos,
    user_profile,
    users,
)



app = FastAPI(
    title="AI",
    description="AI sample",
    version="1.0.0")

# CORS_ORIGINS is read on every request (cors.py): from wrangler.jsonc `vars`
# in a Worker, or from .env locally. A fixed list built at import time never
# saw the Worker's vars, so the deployed UI would have been blocked.
app.add_middleware(EnvCORSMiddleware)


# Register routers under /api (e.g. /api/health, /api/me, /api/users) —
# leaves room for the Worker to serve non-API paths (static assets, etc.)
# from the same origin later without colliding with these routes.
app.include_router(health.router, prefix="/api")
app.include_router(me.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(user_profile.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(users.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(chats.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(assistant.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(todos.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(tags.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(groups.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(posts.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(post_comments.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(media.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(timeline.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(admin.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(
    engagement_analytics.router, prefix="/api", dependencies=[Depends(get_authenticated_user)]
)

register_error_handlers(app)
