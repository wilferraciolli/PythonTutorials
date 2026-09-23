import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import get_authenticated_user
from routers import chats, health, me, user_profile, users



app = FastAPI(
    title="Groq AI",
    description="Groq AI sample",
    version="1.0.0")

# The Clerk token travels as an `Authorization: Bearer …` header, not a
# cookie, so `allow_credentials` stays False — the browser doesn't need to
# send/receive cookies cross-origin for this to work.
# CORS_ORIGINS is read from os.environ (config.py's _load_dotenv()
# populates it for local runs), not via config.get_config() — that needs a
# Request, and CORSMiddleware is built once at import time, before any
# request exists. That also means a wrangler.jsonc `vars` entry would NOT
# reach this: per config.py, Cloudflare injects vars into
# request.scope["env"], not into os.environ. So CORS_ORIGINS (see .env) only
# takes effect for local uvicorn/Docker runs; empty means no cross-origin
# access.
_cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()]

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
app.include_router(chats.router, prefix="/api", dependencies=[Depends(get_authenticated_user)])
