import redis.asyncio as aioredis

from app.domain.interfaces.cache import CacheInterface


class RedisCache(CacheInterface):
    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        result = await self._client.get(key)
        if isinstance(result, bytes):
            return result.decode()
        return result  # type: ignore[return-value]

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def health_check(self) -> bool:
        try:
            return bool(await self._client.ping())
        except (aioredis.ConnectionError, aioredis.TimeoutError, OSError):
            return False
