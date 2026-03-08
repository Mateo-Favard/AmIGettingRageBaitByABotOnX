"""Tests for the AI content analyzer (mocked model)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.domain.interfaces.analyzer import AnalysisInput
from app.domain.models.twitter import TweetData, TwitterProfile
from app.infrastructure.ml.analyzers.ai_content import AIContentAnalyzer

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
            content=f"Tweet numéro {i} avec du texte en français.",
            posted_at=datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=i),
        )
        for i in range(count)
    ]


@pytest.fixture
def mock_analyzer():
    """Create an AIContentAnalyzer with mocked pipeline."""
    analyzer = AIContentAnalyzer.__new__(AIContentAnalyzer)
    mock_pipe = MagicMock()
    analyzer._pipeline = mock_pipe
    yield analyzer, mock_pipe


class TestAIContentAnalyzer:
    async def test_all_ai_detected(self, mock_analyzer):
        analyzer, pipe = mock_analyzer
        pipe.return_value = [{"label": "LABEL_1", "score": 0.95}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        assert result.score > 80
        assert result.details["mean_ai_probability"] > 0.9

    async def test_all_human(self, mock_analyzer):
        analyzer, pipe = mock_analyzer
        pipe.return_value = [{"label": "LABEL_0", "score": 0.95}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        assert result.score < 20
        assert result.details["mean_ai_probability"] < 0.1

    async def test_mixed_detection(self, mock_analyzer):
        analyzer, pipe = mock_analyzer
        pipe.return_value = [
            {"label": "LABEL_1", "score": 0.9},
            {"label": "LABEL_0", "score": 0.8},
            {"label": "LABEL_1", "score": 0.7},
            {"label": "LABEL_0", "score": 0.9},
            {"label": "LABEL_1", "score": 0.85},
        ]

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(5), following=[])
        result = await analyzer.analyze(data)

        assert 20 < result.score < 80

    async def test_no_tweets(self, mock_analyzer):
        analyzer, pipe = mock_analyzer

        data = AnalysisInput(profile=PROFILE, tweets=[], following=[])
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1
        pipe.assert_not_called()

    async def test_name_and_version(self, mock_analyzer):
        analyzer, _ = mock_analyzer
        assert analyzer.name == "ai_content"
        assert analyzer.version == "2.0.0"
