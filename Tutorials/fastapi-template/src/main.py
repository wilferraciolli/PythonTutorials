from fastapi import Depends, FastAPI
from wiltech_labs_auth import get_authenticated_user, require_admin
from wiltech_labs_core import EnvCORSMiddleware, health_router, register_error_handlers

from shared.settings.region import system_settings_router
from users.profiles import me_router, user_profile_router
from users import user_router
from users.settings import user_settings_router

app = FastAPI(
    title="FastAPI Template",
    description="Portable FastAPI starter: Clerk auth, SQLite/D1 database layer, users resource",
    version="0.1.0")

# AppError subclasses (NotFoundError, ConflictError, ...) raised by services
# become `{"detail": ...}` with their status code.
register_error_handlers(app)

# CORS_ORIGINS (comma-separated) is read per request, so it works from .env
# for uvicorn/Docker and from wrangler.jsonc `vars` in a Worker (which only
# exist on the request). The Clerk token travels as an `Authorization:
# Bearer …` header, not a cookie, so credentials stay off. The default only
# covers `ng serve` talking to a local run; set CORS_ORIGINS for a deployed UI.
app.add_middleware(EnvCORSMiddleware, default_origins="http://localhost:4200")


# Register routers under /api (e.g. /api/health, /api/me, /api/users) —
# leaves room for the Worker to serve non-API paths (static assets, etc.)
# from the same origin later without colliding with these routes.
app.include_router(health_router(), prefix="/api")
app.include_router(me_router.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(user_profile_router.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(user_router.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(user_settings_router.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(system_settings_router.router, prefix="/api", dependencies=[Depends(require_admin)])
