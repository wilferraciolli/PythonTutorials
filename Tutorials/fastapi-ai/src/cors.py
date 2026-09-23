import os
from typing import Dict, Tuple

from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


def allowed_origins(scope: Scope) -> Tuple[str, ...]:
    """
    CORS_ORIGINS for this request: from the Worker env (wrangler.jsonc `vars`,
    which Cloudflare puts in scope["env"]) or, for local uvicorn/Docker, from
    os.environ (.env). Comma-separated; empty means no cross-origin access.
    """
    raw = None
    env = scope.get("env")
    if env is not None:
        raw = getattr(env, "CORS_ORIGINS", None)
    if raw is None:
        raw = os.environ.get("CORS_ORIGINS", "")
    return tuple(origin.strip() for origin in str(raw).split(",") if origin.strip())


class EnvCORSMiddleware:
    """
    Starlette's CORSMiddleware, with the allowed origins read per request.

    CORSMiddleware takes a fixed list when the app is built, but in a Worker
    the vars only exist on the request (config.py), so a list read at import
    time was always empty there. This builds one CORSMiddleware per distinct
    origins value and reuses it.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._by_origins: Dict[Tuple[str, ...], CORSMiddleware] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        origins = allowed_origins(scope)
        middleware = self._by_origins.get(origins)
        if middleware is None:
            # The Clerk token travels as an `Authorization: Bearer …` header, not a
            # cookie, so credentials stay off.
            middleware = CORSMiddleware(
                self.app,
                allow_origins=list(origins),
                allow_credentials=False,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            self._by_origins[origins] = middleware
        await middleware(scope, receive, send)
