from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """A business-rule failure a service raises; main.py maps it to an HTTP status."""

    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class InvalidInputError(AppError):
    """Well-formed input that refers to something that doesn't exist (e.g. an unknown user id)."""

    status_code = 422


class UpstreamError(AppError):
    """A third-party API (Unsplash, Giphy) failed."""

    status_code = 502


class NotConfiguredError(AppError):
    """A feature's key isn't set (e.g. UNSPLASH_ACCESS_KEY)."""

    status_code = 503


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
