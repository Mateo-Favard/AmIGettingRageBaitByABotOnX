import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_analysis_service, get_cache, get_settings_dep
from app.domain.interfaces.cache import CacheInterface
from app.domain.interfaces.repositories import AccountRepositoryInterface
from app.domain.models.twitter import AnalysisResultData, TweetData, TwitterProfile
from app.domain.services.analysis import AnalysisService
from app.infrastructure.twitter.mock_client import MockTwitterClient
from app.main import create_app

# --- Test settings ---


def _test_settings() -> Settings:
    return Settings(
        environment="testing",
        debug=False,
        secret_key="test-secret-key",  # type: ignore[arg-type]
        database_url="postgresql+asyncpg://amirb:change_me_in_production@localhost:5432/amirb_db",  # type: ignore[arg-type]
        redis_url="redis://localhost:6379/0",
        twitter_api_key="",  # type: ignore[arg-type]
    )


# --- In-memory cache for tests ---


class FakeCache(CacheInterface):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def health_check(self) -> bool:
        return True


# --- In-memory repository for tests ---


class FakeAccountRepository(AccountRepositoryInterface):
    def __init__(self) -> None:
        self._accounts: dict[str, tuple[uuid.UUID, TwitterProfile]] = {}
        self._tweets: dict[uuid.UUID, list[TweetData]] = {}
        self._analyses: list[AnalysisResultData] = []

    async def get_by_handle(
        self,
        handle: str,
    ) -> tuple[uuid.UUID, TwitterProfile] | None:
        return self._accounts.get(handle)

    async def upsert(
        self,
        profile: TwitterProfile,
    ) -> uuid.UUID:
        existing = self._accounts.get(profile.handle)
        account_id = existing[0] if existing else uuid.uuid4()
        self._accounts[profile.handle] = (account_id, profile)
        return account_id

    async def save_tweets(
        self,
        account_id: uuid.UUID,
        tweets: list[TweetData],
    ) -> None:
        self._tweets[account_id] = tweets

    async def save_analysis(
        self,
        result: AnalysisResultData,
    ) -> None:
        self._analyses.append(result)

    async def get_latest_analysis(
        self,
        handle: str,
    ) -> AnalysisResultData | None:
        matching = [a for a in self._analyses if a.handle == handle]
        if not matching:
            return None
        return max(matching, key=lambda a: a.analyzed_at)


# --- Fixtures ---


@pytest.fixture(scope="session")
def event_loop():  # type: ignore[no-untyped-def]
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    return _test_settings()


@pytest.fixture
def fake_cache() -> FakeCache:
    return FakeCache()


@pytest.fixture
def fake_repo() -> FakeAccountRepository:
    return FakeAccountRepository()


@pytest.fixture
async def client(
    fake_cache: FakeCache,
    fake_repo: FakeAccountRepository,
) -> AsyncGenerator[AsyncClient]:
    settings = _test_settings()
    mock_twitter = MockTwitterClient()

    app = create_app()

    app.dependency_overrides[get_settings_dep] = lambda: settings
    app.dependency_overrides[get_cache] = lambda: fake_cache

    def _analysis_service_override() -> AnalysisService:
        return AnalysisService(
            twitter_client=mock_twitter,
            account_repo=fake_repo,
            cache=fake_cache,
            cache_ttl_seconds=settings.analysis_cache_ttl_seconds,
        )

    app.dependency_overrides[get_analysis_service] = _analysis_service_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
