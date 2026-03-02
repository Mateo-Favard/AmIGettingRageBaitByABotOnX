from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.dependencies import get_cache, get_db_session
from app.domain.interfaces.cache import CacheInterface

router = APIRouter()


async def _check_database(session: AsyncSession) -> str:
    try:
        await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"


async def _check_cache(cache: CacheInterface) -> str:
    try:
        healthy = await cache.health_check()
        return "ok" if healthy else "unavailable"
    except Exception:
        return "unavailable"


@router.get("/health")
async def health_check(
    session: AsyncSession = Depends(get_db_session),  # noqa: B008
    cache: CacheInterface = Depends(get_cache),  # noqa: B008
) -> JSONResponse:
    db_status = await _check_database(session)
    cache_status = await _check_cache(cache)

    checks: dict[str, Any] = {
        "database": db_status,
        "redis": cache_status,
        "ml_models": "not_loaded",
    }

    all_critical_ok = db_status == "ok"
    status = "healthy" if all_critical_ok else "degraded"
    status_code = 200 if all_critical_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "checks": checks,
            "version": "0.1.0",
        },
    )
