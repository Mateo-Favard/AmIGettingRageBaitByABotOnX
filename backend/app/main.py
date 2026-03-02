from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.core.security import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.is_production = settings.is_production
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Am I Getting Rage Bait by a Bot on X?",
        version="0.1.0",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        lifespan=lifespan,
    )

    # --- Rate limiting ---
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # --- Middleware (order matters: last added = first executed) ---
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routers ---
    app.include_router(api_v1_router)

    return app


def get_app() -> FastAPI:
    return create_app()


app = get_app()
