"""Tests for the network heuristic analyzer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.domain.interfaces.analyzer import AnalysisInput
from app.domain.interfaces.repositories import AccountRepositoryInterface
from app.domain.models.twitter import AnalysisResultData, TweetData, TwitterProfile
from app.infrastructure.ml.analyzers.network import NetworkAnalyzer

PROFILE = TwitterProfile(
    handle="test_user",
    display_name="Test",
    bio="",
    followers_count=1000,
    following_count=500,
    tweets_count=200,
)


class FakeAccountRepo(AccountRepositoryInterface):
    def __init__(self) -> None:
        self._analyses: dict[str, AnalysisResultData] = {}

    def add_analysis(self, handle: str, score: float) -> None:
        self._analyses[handle] = AnalysisResultData(
            account_id=uuid.uuid4(),
            handle=handle,
            composite_score=score,
            analyzed_at=datetime.now(tz=UTC),
        )

    async def get_by_handle(self, handle: str):
        return None

    async def upsert(self, profile: TwitterProfile) -> uuid.UUID:
        return uuid.uuid4()

    async def save_tweets(self, account_id: uuid.UUID, tweets: list[TweetData]) -> None:
        pass

    async def save_analysis(self, result: AnalysisResultData) -> None:
        pass

    async def get_latest_analysis(self, handle: str) -> AnalysisResultData | None:
        return self._analyses.get(handle)


@pytest.fixture
def repo() -> FakeAccountRepo:
    return FakeAccountRepo()


class TestNetworkAnalyzer:
    async def test_no_following(self, repo: FakeAccountRepo):
        analyzer = NetworkAnalyzer(account_repo=repo)
        data = AnalysisInput(profile=PROFILE, tweets=[], following=[])
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1

    async def test_no_repo(self):
        analyzer = NetworkAnalyzer(account_repo=None)
        data = AnalysisInput(profile=PROFILE, tweets=[], following=["a", "b"])
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1

    async def test_cold_start(self, repo: FakeAccountRepo):
        """No followed accounts are in the DB."""
        analyzer = NetworkAnalyzer(account_repo=repo)
        data = AnalysisInput(
            profile=PROFILE,
            tweets=[],
            following=["unknown1", "unknown2", "unknown3"],
        )
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1
        assert result.details.get("reason") == "cold_start"

    async def test_no_suspects(self, repo: FakeAccountRepo):
        """Followed accounts exist but have low scores."""
        repo.add_analysis("friend1", score=20.0)
        repo.add_analysis("friend2", score=30.0)

        analyzer = NetworkAnalyzer(account_repo=repo)
        data = AnalysisInput(
            profile=PROFILE,
            tweets=[],
            following=["friend1", "friend2", "unknown"],
        )
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.details.get("suspect_count") == 0

    async def test_some_suspects(self, repo: FakeAccountRepo):
        """Some followed accounts are known rage-bait."""
        repo.add_analysis("ragebait1", score=85.0)
        repo.add_analysis("ragebait2", score=90.0)
        repo.add_analysis("normal", score=20.0)

        analyzer = NetworkAnalyzer(account_repo=repo)
        data = AnalysisInput(
            profile=PROFILE,
            tweets=[],
            following=["ragebait1", "ragebait2", "normal", "unknown"],
        )
        result = await analyzer.analyze(data)

        assert result.score > 0
        assert result.details.get("suspect_count") == 2
        assert result.details.get("analyzed_in_db") == 3

    async def test_all_suspects(self, repo: FakeAccountRepo):
        """All followed accounts are rage-bait."""
        for i in range(5):
            repo.add_analysis(f"bot{i}", score=80.0 + i)

        analyzer = NetworkAnalyzer(account_repo=repo)
        data = AnalysisInput(
            profile=PROFILE,
            tweets=[],
            following=[f"bot{i}" for i in range(5)],
        )
        result = await analyzer.analyze(data)

        assert result.score > 80
        assert result.details.get("suspect_count") == 5

    async def test_name_and_version(self):
        analyzer = NetworkAnalyzer()
        assert analyzer.name == "network"
        assert analyzer.version == "1.0.0"

    async def test_health_check(self):
        analyzer = NetworkAnalyzer()
        assert await analyzer.health_check() is True
