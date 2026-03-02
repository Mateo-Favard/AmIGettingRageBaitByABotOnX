from collections.abc import AsyncGenerator
from functools import lru_cache

import redis.asyncio as aioredis

from app.config import get_settings


@lru_cache
def _get_redis_client() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
    )


async def get_redis() -> AsyncGenerator[aioredis.Redis]:
    yield _get_redis_client()


async def redis_health_check() -> bool:
    try:
        client = _get_redis_client()
        return bool(await client.ping())
    except (aioredis.ConnectionError, aioredis.TimeoutError, OSError):
        return False
