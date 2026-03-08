import uuid
from datetime import UTC, datetime

import pytest

from app.domain.models.twitter import AnalysisResultData, TweetData, TwitterProfile


class TestTwitterProfile:
    def test_create_profile(self) -> None:
        profile = TwitterProfile(
            handle="testuser",
            display_name="Test User",
            bio="A test bio",
            followers_count=100,
            following_count=50,
            tweets_count=200,
        )
        assert profile.handle == "testuser"
        assert profile.display_name == "Test User"
        assert profile.followers_count == 100
        assert profile.profile_image_url == ""
        assert profile.account_created_at is None

    def test_profile_is_frozen(self) -> None:
        profile = TwitterProfile(
            handle="testuser",
            display_name="Test User",
            bio="A test bio",
            followers_count=100,
            following_count=50,
            tweets_count=200,
        )
        with pytest.raises(AttributeError):
            profile.handle = "changed"  # type: ignore[misc]


class TestTweetData:
    def test_create_tweet(self) -> None:
        now = datetime.now(tz=UTC)
        tweet = TweetData(
            twitter_id="123456",
            content="Hello world",
            posted_at=now,
            likes_count=10,
        )
        assert tweet.twitter_id == "123456"
        assert tweet.content == "Hello world"
        assert tweet.likes_count == 10
        assert tweet.retweets_count == 0
        assert tweet.replies_count == 0

    def test_tweet_is_frozen(self) -> None:
        tweet = TweetData(
            twitter_id="123456",
            content="Hello world",
            posted_at=datetime.now(tz=UTC),
        )
        with pytest.raises(AttributeError):
            tweet.content = "changed"  # type: ignore[misc]


class TestAnalysisResultData:
    def test_create_analysis(self) -> None:
        account_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        result = AnalysisResultData(
            account_id=account_id,
            handle="testuser",
            composite_score=42.5,
            analyzed_at=now,
            behavioral_score=30.0,
        )
        assert result.account_id == account_id
        assert result.handle == "testuser"
        assert result.composite_score == 42.5
        assert result.behavioral_score == 30.0
        assert result.ai_content_score is None
        assert result.details == {}
        assert result.model_versions == {}

    def test_analysis_is_frozen(self) -> None:
        result = AnalysisResultData(
            account_id=uuid.uuid4(),
            handle="testuser",
            composite_score=42.5,
            analyzed_at=datetime.now(tz=UTC),
        )
        with pytest.raises(AttributeError):
            result.composite_score = 99.0  # type: ignore[misc]

    def test_score_range(self) -> None:
        result = AnalysisResultData(
            account_id=uuid.uuid4(),
            handle="testuser",
            composite_score=0.0,
            analyzed_at=datetime.now(tz=UTC),
        )
        assert 0.0 <= result.composite_score <= 100.0
