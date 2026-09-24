import json
import logging
import os
from typing import Dict, Tuple

from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


def _catch_errors(app: ASGIApp) -> ASGIApp:
    """
    Turn an unhandled exception into a 500 JSON reply *inside* the CORS layer.

    Starlette's own 500 handler sits outside every middleware, so its reply has
    no CORS headers and a browser reports it as "can't reach the server"
    (status 0) instead of showing the error.
    """

    async def wrapped(scope: Scope, receive: Receive, send: Send) -> None:
        started = False

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await app(scope, receive, tracking_send)
        except Exception:
            logger.exception("unhandled error on %s %s", scope.get("method"), scope.get("path"))
            if started:
                raise
            body = json.dumps({"detail": "Something went wrong on the server."}).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
                }
            )
            await send({"type": "http.response.body", "body": body})

    return wrapped


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
                _catch_errors(self.app),
                allow_origins=list(origins),
                allow_credentials=False,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            self._by_origins[origins] = middleware
        await middleware(scope, receive, send)
