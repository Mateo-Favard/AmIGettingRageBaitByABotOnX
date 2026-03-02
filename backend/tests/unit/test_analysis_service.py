import uuid

import pytest

from app.domain.interfaces.cache import CacheInterface
from app.domain.interfaces.repositories import AccountRepositoryInterface
from app.domain.models.twitter import AnalysisResultData, TweetData, TwitterProfile
from app.domain.services.analysis import AnalysisService, _compute_placeholder_score
from app.infrastructure.twitter.mock_client import MockTwitterClient

# --- Fakes ---


class FakeCache(CacheInterface):
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl_seconds: int,
    ) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def health_check(self) -> bool:
        return True


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


@pytest.fixture
def fake_cache() -> FakeCache:
    return FakeCache()


@pytest.fixture
def fake_repo() -> FakeAccountRepository:
    return FakeAccountRepository()


@pytest.fixture
def mock_twitter() -> MockTwitterClient:
    return MockTwitterClient()


@pytest.fixture
def service(
    mock_twitter: MockTwitterClient,
    fake_repo: FakeAccountRepository,
    fake_cache: FakeCache,
) -> AnalysisService:
    return AnalysisService(
        twitter_client=mock_twitter,
        account_repo=fake_repo,
        cache=fake_cache,
        cache_ttl_seconds=3600,
    )


# --- Tests ---


class TestPlaceholderScore:
    def test_low_ratio(self) -> None:
        profile = TwitterProfile(
            handle="normal",
            display_name="Normal",
            bio="",
            followers_count=100,
            following_count=90,
            tweets_count=100,
        )
        score = _compute_placeholder_score(profile)
        assert score < 5.0

    def test_high_ratio(self) -> None:
        profile = TwitterProfile(
            handle="suspect",
            display_name="Suspect",
            bio="",
            followers_count=50_000,
            following_count=10,
            tweets_count=100_000,
        )
        score = _compute_placeholder_score(profile)
        assert score > 2.0

    def test_zero_following(self) -> None:
        profile = TwitterProfile(
            handle="nofollow",
            display_name="NoFollow",
            bio="",
            followers_count=10_000,
            following_count=0,
            tweets_count=100,
        )
        score = _compute_placeholder_score(profile)
        assert score == 50.0

    def test_score_capped_at_50(self) -> None:
        profile = TwitterProfile(
            handle="mega",
            display_name="Mega",
            bio="",
            followers_count=1_000_000,
            following_count=1,
            tweets_count=100,
        )
        score = _compute_placeholder_score(profile)
        assert score <= 50.0


class TestAnalysisService:
    async def test_analyze_normal_user(
        self,
        service: AnalysisService,
    ) -> None:
        result, cached = await service.analyze("devweb_alex")
        assert not cached
        assert result.handle == "devweb_alex"
        assert 0 <= result.composite_score <= 100

    async def test_analyze_suspect_user(
        self,
        service: AnalysisService,
    ) -> None:
        result, cached = await service.analyze("suspect_bot42")
        assert not cached
        assert result.handle == "suspect_bot42"
        assert result.composite_score > 0

    async def test_second_call_returns_cached(
        self,
        service: AnalysisService,
    ) -> None:
        result1, cached1 = await service.analyze("devweb_alex")
        assert not cached1

        result2, cached2 = await service.analyze("devweb_alex")
        assert cached2
        assert result2.handle == result1.handle
        assert result2.composite_score == result1.composite_score

    async def test_force_bypasses_cache(
        self,
        service: AnalysisService,
    ) -> None:
        await service.analyze("devweb_alex")

        _result, cached = await service.analyze(
            "devweb_alex",
            force=True,
        )
        assert not cached

    async def test_analysis_persisted(
        self,
        service: AnalysisService,
        fake_repo: FakeAccountRepository,
    ) -> None:
        await service.analyze("devweb_alex")
        assert len(fake_repo._analyses) == 1
        assert fake_repo._analyses[0].handle == "devweb_alex"

    async def test_account_upserted(
        self,
        service: AnalysisService,
        fake_repo: FakeAccountRepository,
    ) -> None:
        await service.analyze("devweb_alex")
        result = await fake_repo.get_by_handle("devweb_alex")
        assert result is not None

    async def test_tweets_saved(
        self,
        service: AnalysisService,
        fake_repo: FakeAccountRepository,
    ) -> None:
        await service.analyze("devweb_alex")
        assert len(fake_repo._tweets) == 1
