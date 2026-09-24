from fastapi import Depends, FastAPI

from admin import admin_router
from admin.analytics import engagement_router
from assistant import assistant_router
from chats import chat_router
from core.common.errors import register_error_handlers
from core.config.cors import EnvCORSMiddleware
from core.security.auth import get_authenticated_user
from groups import group_router
from groups.posts import post_router
from groups.posts.comments import comment_router
from media import media_router
from metrics import status_router
from tags import tag_router
from timeline import timeline_router
from todos import todo_router
from users import user_router
from users.dependencies import ensure_current_user
from users.profiles import me_router, user_profile_router

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
# Every router except the health check requires a signed-in caller.
# ensure_current_user creates the caller's user on first sight (as /me
# does) before any route dependency runs, so get_caller always finds them.
app.include_router(status_router.router, prefix="/api")
app.include_router(me_router.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])

for router in (
    user_profile_router.router,
    user_router.router,
    chat_router.router,
    assistant_router.router,
    todo_router.router,
    tag_router.router,
    group_router.router,
    post_router.router,
    comment_router.router,
    media_router.router,
    timeline_router.router,
    admin_router.router,
    engagement_router.router,
):
    app.include_router(
        router,
        prefix="/api",
        dependencies=[Depends(get_authenticated_user), Depends(ensure_current_user)],
    )

register_error_handlers(app)
