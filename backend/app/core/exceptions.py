import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# --- Base ---


class AppError(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        self.message = message or self.__class__.message
        self.details = kwargs
        super().__init__(self.message)


# --- Client errors ---


class ValidationError(AppError):
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Invalid input"


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMITED"
    message = "Too many requests"


# --- Server errors ---


class ExternalServiceError(AppError):
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "External service unavailable"


class TwitterAPIError(ExternalServiceError):
    error_code = "TWITTER_API_ERROR"
    message = "Twitter API error"


class AnalysisError(AppError):
    status_code = 500
    error_code = "ANALYSIS_ERROR"
    message = "Analysis failed"


class MLPipelineError(AnalysisError):
    error_code = "ML_PIPELINE_ERROR"
    message = "ML pipeline error"


# --- Handlers ---


def _build_error_response(
    error_code: str,
    message: str,
    status_code: int,
    *,
    is_production: bool,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message if not is_production else _safe_message(error_code),
        }
    }
    if details and not is_production:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def _safe_message(error_code: str) -> str:
    safe_messages: dict[str, str] = {
        "VALIDATION_ERROR": "Invalid input",
        "NOT_FOUND": "Resource not found",
        "RATE_LIMITED": "Too many requests, please try again later",
        "EXTERNAL_SERVICE_ERROR": "An external service is temporarily unavailable",
        "TWITTER_API_ERROR": "An external service is temporarily unavailable",
        "ANALYSIS_ERROR": "Analysis could not be completed",
        "ML_PIPELINE_ERROR": "Analysis could not be completed",
        "INTERNAL_ERROR": "An unexpected error occurred",
    }
    return safe_messages.get(error_code, "An unexpected error occurred")


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "AppError [%s] %s: %s | details=%s",
        request_id,
        exc.error_code,
        exc.message,
        exc.details,
    )
    is_production = getattr(request.app.state, "is_production", False)
    return _build_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        is_production=is_production,
        details=exc.details,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.exception("Unhandled exception [%s]", request_id)
    is_production = getattr(request.app.state, "is_production", False)
    return _build_error_response(
        error_code="INTERNAL_ERROR",
        message=str(exc),
        status_code=500,
        is_production=is_production,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)
