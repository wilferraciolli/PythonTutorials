import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import get_authenticated_user
from routers import health, me, user_profile, users



app = FastAPI(
    title="FastAPI Template",
    description="Portable FastAPI starter: Clerk auth, SQLite/D1 database layer, users resource",
    version="0.1.0")

# The Clerk token travels as an `Authorization: Bearer …` header, not a
# cookie, so `allow_credentials` stays False — the browser doesn't need to
# send/receive cookies cross-origin for this to work.
# CORS_ORIGINS is read from os.environ (config.py's _load_dotenv()
# populates it for local runs), not via config.get_config() — that needs a
# Request, and CORSMiddleware is built once at import time, before any
# request exists. That also means a wrangler.jsonc `vars` entry would NOT
# reach this: per config.py, Cloudflare injects vars into
# request.scope["env"], not into os.environ. TODO: once the showcase UI
# has a deployed (Pages) origin, add it to the default list below directly
# — this default only covers `ng serve` talking to a local uvicorn/Docker
# run.
_cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://localhost:4200").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers under /api (e.g. /api/health, /api/me, /api/users) —
# leaves room for the Worker to serve non-API paths (static assets, etc.)
# from the same origin later without colliding with these routes.
app.include_router(health.router, prefix="/api")
app.include_router(me.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(user_profile.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
app.include_router(users.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
