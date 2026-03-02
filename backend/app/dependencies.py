from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.domain.interfaces.cache import CacheInterface
from app.domain.interfaces.repositories import AccountRepositoryInterface
from app.domain.interfaces.twitter import TwitterClientInterface
from app.domain.services.analysis import AnalysisService
from app.infrastructure.db.repositories.account import AccountRepository
from app.infrastructure.db.session import get_db_session as _get_db_session
from app.infrastructure.redis.cache import RedisCache
from app.infrastructure.redis.client import _get_redis_client
from app.infrastructure.redis.client import get_redis as _get_redis


async def get_settings_dep() -> Settings:
    return get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async for session in _get_db_session():
        yield session


async def get_redis() -> AsyncGenerator[Redis]:
    async for client in _get_redis():
        yield client


async def get_cache() -> AsyncGenerator[CacheInterface]:
    yield RedisCache(_get_redis_client())


async def get_twitter_client() -> TwitterClientInterface:
    settings = get_settings()

    # 1. API payante (twitterapi.io)
    api_key = settings.twitter_api_key.get_secret_value()
    if api_key and not api_key.startswith("your_"):
        from app.infrastructure.twitter.api_client import TwitterAPIClient

        return TwitterAPIClient(
            api_key=api_key,
            timeout=settings.twitter_api_timeout_seconds,
            max_retries=settings.twitter_api_max_retries,
        )

    # 2. Twikit (gratuit, credentials Twitter)
    if settings.has_twitter_credentials:
        from app.infrastructure.twitter.twikit_client import TwikitClient

        return TwikitClient(
            username=settings.twitter_username.get_secret_value(),
            email=settings.twitter_email.get_secret_value(),
            password=settings.twitter_password.get_secret_value(),
        )

    # 3. Mock (fallback dev)
    from app.infrastructure.twitter.mock_client import MockTwitterClient

    return MockTwitterClient()


async def get_account_repository(
    session: AsyncSession,
) -> AccountRepositoryInterface:
    return AccountRepository(session)


async def get_analysis_service() -> AsyncGenerator[AnalysisService]:
    settings = get_settings()
    twitter_client = await get_twitter_client()
    cache = RedisCache(_get_redis_client())

    async for session in _get_db_session():
        repo = AccountRepository(session)
        yield AnalysisService(
            twitter_client=twitter_client,
            account_repo=repo,
            cache=cache,
            cache_ttl_seconds=settings.analysis_cache_ttl_seconds,
        )
