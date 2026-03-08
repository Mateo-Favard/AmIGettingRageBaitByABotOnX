from __future__ import annotations

import re
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import Response

from app.core.security import limiter
from app.dependencies import get_account_repository, get_cache, get_db_session

if TYPE_CHECKING:
    from app.domain.interfaces.cache import CacheInterface
    from app.domain.interfaces.repositories import AccountRepositoryInterface

router = APIRouter()

_HANDLE_RE = re.compile(r"^[a-zA-Z0-9_]{1,15}$")


@router.delete("/account/{handle}", status_code=204)
@limiter.limit("5/minute")
async def delete_account(
    request: Request,
    handle: str,
    session: object = Depends(get_db_session),
    cache: CacheInterface = Depends(get_cache),  # noqa: B008
) -> Response:
    """RGPD — Delete all data associated with a Twitter handle."""
    if not _HANDLE_RE.match(handle):
        raise HTTPException(status_code=400, detail="Invalid handle format")

    repo: AccountRepositoryInterface = await get_account_repository(session)  # type: ignore[arg-type]
    deleted = await repo.delete_by_handle(handle)

    if deleted:
        await cache.delete(f"analysis:{handle}")

    return Response(status_code=204)
