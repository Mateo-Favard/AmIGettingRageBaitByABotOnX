import uuid
from datetime import UTC, datetime

import pytest

from app.domain.interfaces.repositories import (
    AccountRepositoryInterface,
)
from app.domain.models.twitter import (
    AnalysisResultData,
    TweetData,
    TwitterProfile,
)


class FakeAccountRepository(AccountRepositoryInterface):
    """In-memory repository for testing."""

    def __init__(self) -> None:
        self._accounts: dict[str, tuple[uuid.UUID, TwitterProfile]] = {}
        self._tweets: dict[uuid.UUID, list[TweetData]] = {}
        self._analyses: list[AnalysisResultData] = []

    async def get_by_handle(
        self, handle: str
    ) -> tuple[uuid.UUID, TwitterProfile] | None:
        return self._accounts.get(handle)

    async def upsert(self, profile: TwitterProfile) -> uuid.UUID:
        existing = self._accounts.get(profile.handle)
        account_id = existing[0] if existing else uuid.uuid4()
        self._accounts[profile.handle] = (account_id, profile)
        return account_id

    async def save_tweets(self, account_id: uuid.UUID, tweets: list[TweetData]) -> None:
        self._tweets[account_id] = tweets

    async def save_analysis(self, result: AnalysisResultData) -> None:
        self._analyses.append(result)

    async def get_latest_analysis(self, handle: str) -> AnalysisResultData | None:
        matching = [a for a in self._analyses if a.handle == handle]
        if not matching:
            return None
        return max(matching, key=lambda a: a.analyzed_at)


@pytest.fixture
def fake_repo() -> FakeAccountRepository:
    return FakeAccountRepository()


def _sample_profile(
    handle: str = "testuser",
) -> TwitterProfile:
    return TwitterProfile(
        handle=handle,
        display_name="Test User",
        bio="A test bio",
        followers_count=100,
        following_count=50,
        tweets_count=200,
    )


class TestFakeAccountRepository:
    async def test_upsert_creates_account(
        self, fake_repo: FakeAccountRepository
    ) -> None:
        profile = _sample_profile()
        account_id = await fake_repo.upsert(profile)
        assert isinstance(account_id, uuid.UUID)

    async def test_get_by_handle_after_upsert(
        self, fake_repo: FakeAccountRepository
    ) -> None:
        profile = _sample_profile()
        await fake_repo.upsert(profile)
        result = await fake_repo.get_by_handle("testuser")
        assert result is not None
        _account_id, fetched_profile = result
        assert fetched_profile.handle == "testuser"

    async def test_get_by_handle_not_found(
        self, fake_repo: FakeAccountRepository
    ) -> None:
        result = await fake_repo.get_by_handle("nonexistent")
        assert result is None

    async def test_upsert_updates_existing(
        self, fake_repo: FakeAccountRepository
    ) -> None:
        profile1 = _sample_profile()
        id1 = await fake_repo.upsert(profile1)

        profile2 = TwitterProfile(
            handle="testuser",
            display_name="Updated Name",
            bio="Updated bio",
            followers_count=200,
            following_count=60,
            tweets_count=300,
        )
        id2 = await fake_repo.upsert(profile2)

        assert id1 == id2
        result = await fake_repo.get_by_handle("testuser")
        assert result is not None
        _, p = result
        assert p.display_name == "Updated Name"

    async def test_save_and_get_analysis(
        self, fake_repo: FakeAccountRepository
    ) -> None:
        account_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        analysis = AnalysisResultData(
            account_id=account_id,
            handle="testuser",
            composite_score=42.5,
            analyzed_at=now,
        )
        await fake_repo.save_analysis(analysis)
        latest = await fake_repo.get_latest_analysis("testuser")
        assert latest is not None
        assert latest.composite_score == 42.5

    async def test_get_latest_analysis_returns_most_recent(
        self, fake_repo: FakeAccountRepository
    ) -> None:
        account_id = uuid.uuid4()
        old = AnalysisResultData(
            account_id=account_id,
            handle="testuser",
            composite_score=30.0,
            analyzed_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        new = AnalysisResultData(
            account_id=account_id,
            handle="testuser",
            composite_score=50.0,
            analyzed_at=datetime(2024, 6, 1, tzinfo=UTC),
        )
        await fake_repo.save_analysis(old)
        await fake_repo.save_analysis(new)
        latest = await fake_repo.get_latest_analysis("testuser")
        assert latest is not None
        assert latest.composite_score == 50.0

    async def test_save_tweets(self, fake_repo: FakeAccountRepository) -> None:
        account_id = uuid.uuid4()
        tweets = [
            TweetData(
                twitter_id="t1",
                content="Hello",
                posted_at=datetime.now(tz=UTC),
            ),
        ]
        await fake_repo.save_tweets(account_id, tweets)
        assert account_id in fake_repo._tweets
        assert len(fake_repo._tweets[account_id]) == 1
