import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base for errors that should become an HTTP response.

    Domain modules can subclass this and keep their own exception types.
    """

    status_code = 500
    detail = "Internal server error"

    def __init__(self, detail=None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = 400
    detail = "Bad request"


class NotAuthenticatedError(AppError):
    status_code = 401
    detail = "Not authenticated"


class ConfigurationError(AppError):
    status_code = 500
    detail = "Server configuration is invalid"


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"Cache-Control": "no-store"},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"Cache-Control": "no-store"},
        )
