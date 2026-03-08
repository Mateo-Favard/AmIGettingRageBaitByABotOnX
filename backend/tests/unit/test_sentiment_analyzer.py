"""Tests for the sentiment analyzer (mocked model)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.domain.interfaces.analyzer import AnalysisInput
from app.domain.models.twitter import TweetData, TwitterProfile
from app.infrastructure.ml.analyzers.sentiment import SentimentAnalyzer

PROFILE = TwitterProfile(
    handle="test",
    display_name="Test",
    bio="",
    followers_count=1000,
    following_count=500,
    tweets_count=200,
)


def _make_tweets(count: int = 10) -> list[TweetData]:
    return [
        TweetData(
            twitter_id=str(i),
            content=f"Tweet {i}",
            posted_at=datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=i),
        )
        for i in range(count)
    ]


@pytest.fixture
def mock_pipeline():
    """Create a SentimentAnalyzer with mocked HuggingFace pipeline."""
    mock_pipe = MagicMock()
    analyzer = SentimentAnalyzer.__new__(SentimentAnalyzer)
    analyzer._pipeline = mock_pipe
    yield analyzer, mock_pipe


class TestSentimentAnalyzer:
    async def test_all_negative(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "negative", "score": 0.95}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        # negative_ratio=1.0 → 70; neutral_ratio=0.0 → 30; total=100
        assert result.score == 100.0
        assert result.confidence == 0.8

    async def test_all_neutral(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "neutral", "score": 0.90}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        # negative_ratio=0.0 → 0; neutral_ratio=1.0 → 0; total=0
        assert result.score == 0.0

    async def test_all_positive(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "positive", "score": 0.90}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        # negative_ratio=0 → 0; neutral_ratio=0 → 30; total=30
        assert result.score == 30.0

    async def test_mixed_sentiment(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [
            {"label": "negative", "score": 0.9},
            {"label": "neutral", "score": 0.8},
            {"label": "positive", "score": 0.7},
            {"label": "negative", "score": 0.85},
            {"label": "neutral", "score": 0.75},
        ]

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(5), following=[])
        result = await analyzer.analyze(data)

        assert 0 < result.score < 100
        assert result.details["negative_count"] == 2
        assert result.details["neutral_count"] == 2
        assert result.details["positive_count"] == 1

    async def test_no_tweets(self, mock_pipeline):
        analyzer, pipe = mock_pipeline

        data = AnalysisInput(profile=PROFILE, tweets=[], following=[])
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1
        pipe.assert_not_called()

    async def test_confidence_scaling(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "neutral", "score": 0.9}]

        # 1 tweet → confidence 0.2
        data1 = AnalysisInput(profile=PROFILE, tweets=_make_tweets(1), following=[])
        r1 = await analyzer.analyze(data1)
        assert r1.confidence == 0.2

        # 5 tweets → confidence 0.5
        pipe.return_value = [{"label": "neutral", "score": 0.9}] * 5
        data5 = AnalysisInput(profile=PROFILE, tweets=_make_tweets(5), following=[])
        r5 = await analyzer.analyze(data5)
        assert r5.confidence == 0.5

        # 20 tweets → confidence 0.95
        pipe.return_value = [{"label": "neutral", "score": 0.9}] * 20
        data20 = AnalysisInput(profile=PROFILE, tweets=_make_tweets(20), following=[])
        r20 = await analyzer.analyze(data20)
        assert r20.confidence == 0.95

    async def test_name_and_version(self, mock_pipeline):
        analyzer, _ = mock_pipeline
        assert analyzer.name == "sentiment"
        assert analyzer.version == "1.0.0"
