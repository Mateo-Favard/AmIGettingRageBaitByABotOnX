"""Tests for the behavioral heuristic analyzer."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.interfaces.analyzer import AnalysisInput
from app.domain.models.twitter import TweetData, TwitterProfile
from app.infrastructure.ml.analyzers.behavioral import BehavioralAnalyzer


def _make_input(
    followers: int = 1000,
    following: int = 500,
    tweets_count: int = 200,
    account_created_at: datetime | None = datetime(2020, 1, 1, tzinfo=UTC),
    tweets: list[TweetData] | None = None,
) -> AnalysisInput:
    profile = TwitterProfile(
        handle="test",
        display_name="Test",
        bio="Test bio",
        followers_count=followers,
        following_count=following,
        tweets_count=tweets_count,
        account_created_at=account_created_at,
    )
    if tweets is None:
        tweets = [
            TweetData(
                twitter_id=str(i),
                content=f"Tweet {i}",
                posted_at=datetime(2024, 6, 1, 10, 0, tzinfo=UTC)
                + timedelta(hours=i * 3),
                likes_count=10,
                retweets_count=2,
                replies_count=1,
            )
            for i in range(10)
        ]
    return AnalysisInput(profile=profile, tweets=tweets, following=[])


@pytest.fixture
def analyzer() -> BehavioralAnalyzer:
    return BehavioralAnalyzer()


class TestBehavioralAnalyzer:
    async def test_normal_account(self, analyzer: BehavioralAnalyzer):
        data = _make_input(followers=1000, following=500)
        result = await analyzer.analyze(data)

        assert 0 <= result.score <= 100
        assert result.confidence > 0

    async def test_high_follower_ratio(self, analyzer: BehavioralAnalyzer):
        data = _make_input(followers=100_000, following=10)
        result = await analyzer.analyze(data)

        assert result.details.get("follower_ratio_score") is not None
        follower_score = result.details["follower_ratio_score"]
        assert isinstance(follower_score, float)
        assert follower_score > 50

    async def test_zero_following(self, analyzer: BehavioralAnalyzer):
        data = _make_input(followers=50_000, following=0)
        result = await analyzer.analyze(data)

        assert result.score > 0

    async def test_zero_followers(self, analyzer: BehavioralAnalyzer):
        data = _make_input(followers=0, following=100)
        result = await analyzer.analyze(data)

        assert result.details.get("follower_ratio_score") == 0.0

    async def test_no_account_age(self, analyzer: BehavioralAnalyzer):
        data = _make_input(account_created_at=None)
        result = await analyzer.analyze(data)

        assert result.details.get("age_volume_score") is None
        assert result.confidence < 1.0  # Lower because age signal missing

    async def test_bot_like_regularity(self, analyzer: BehavioralAnalyzer):
        # Very regular posting intervals (every 60 seconds exactly)
        tweets = [
            TweetData(
                twitter_id=str(i),
                content=f"Bot tweet {i}",
                posted_at=datetime(2024, 6, 1, tzinfo=UTC) + timedelta(seconds=60 * i),
                likes_count=5,
                retweets_count=1,
                replies_count=0,
            )
            for i in range(20)
        ]
        data = _make_input(tweets=tweets)
        result = await analyzer.analyze(data)

        regularity = result.details.get("regularity_score")
        assert regularity is not None
        assert regularity > 50  # Should detect regular pattern

    async def test_human_like_posting(self, analyzer: BehavioralAnalyzer):
        # Irregular posting intervals
        import random

        random.seed(42)
        tweets = [
            TweetData(
                twitter_id=str(i),
                content=f"Human tweet {i}",
                posted_at=datetime(2024, 6, 1, tzinfo=UTC)
                + timedelta(minutes=random.randint(30, 600) * i),
                likes_count=10,
                retweets_count=3,
                replies_count=2,
            )
            for i in range(10)
        ]
        data = _make_input(tweets=tweets)
        result = await analyzer.analyze(data)

        regularity = result.details.get("regularity_score")
        assert regularity is not None
        assert regularity < 50  # Should detect irregular pattern

    async def test_too_few_tweets_for_regularity(self, analyzer: BehavioralAnalyzer):
        tweets = [
            TweetData(
                twitter_id="1",
                content="Only tweet",
                posted_at=datetime(2024, 6, 1, tzinfo=UTC),
            )
        ]
        data = _make_input(tweets=tweets)
        result = await analyzer.analyze(data)

        assert result.details.get("regularity_score") is None
        assert result.details.get("posting_hours_score") is None

    async def test_24_7_posting(self, analyzer: BehavioralAnalyzer):
        # Tweets spread across all hours
        tweets = [
            TweetData(
                twitter_id=str(i),
                content=f"All hours tweet {i}",
                posted_at=datetime(2024, 6, 1, i, 0, tzinfo=UTC),
                likes_count=5,
                retweets_count=1,
                replies_count=0,
            )
            for i in range(24)
        ]
        data = _make_input(tweets=tweets)
        result = await analyzer.analyze(data)

        hours_score = result.details.get("posting_hours_score")
        assert hours_score is not None
        assert hours_score > 50

    async def test_name_and_version(self, analyzer: BehavioralAnalyzer):
        assert analyzer.name == "behavioral"
        assert analyzer.version == "1.0.0"

    async def test_health_check(self, analyzer: BehavioralAnalyzer):
        assert await analyzer.health_check() is True

    async def test_empty_tweets(self, analyzer: BehavioralAnalyzer):
        data = _make_input(tweets=[])
        result = await analyzer.analyze(data)

        assert 0 <= result.score <= 100
        assert result.confidence < 1.0
