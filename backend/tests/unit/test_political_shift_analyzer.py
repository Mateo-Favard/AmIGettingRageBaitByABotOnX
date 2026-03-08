"""Tests for the political shift analyzer (mocked model)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.domain.interfaces.analyzer import AnalysisInput
from app.domain.models.twitter import TweetData, TwitterProfile
from app.infrastructure.ml.analyzers.political_shift import PoliticalShiftAnalyzer

PROFILE = TwitterProfile(
    handle="test",
    display_name="Test",
    bio="",
    followers_count=1000,
    following_count=500,
    tweets_count=200,
)


def _make_tweets(count: int = 10, span_days: int = 30) -> list[TweetData]:
    return [
        TweetData(
            twitter_id=str(i),
            content=f"Tweet politique {i}",
            posted_at=datetime(2024, 6, 1, tzinfo=UTC)
            + timedelta(days=span_days * i / max(1, count - 1)),
        )
        for i in range(count)
    ]


@pytest.fixture
def mock_pipeline():
    """Create a PoliticalShiftAnalyzer with mocked pipeline."""
    mock_pipe = MagicMock()
    analyzer = PoliticalShiftAnalyzer.__new__(PoliticalShiftAnalyzer)
    analyzer._pipeline = mock_pipe
    yield analyzer, mock_pipe


class TestPoliticalShiftAnalyzer:
    async def test_all_problem(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "problem", "score": 0.9}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        # problem_ratio=1.0 → 60 points + shift_score
        assert result.score >= 60
        assert result.details["problem_count"] == 10
        assert result.details["problem_ratio"] == 1.0

    async def test_all_solution(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "solution", "score": 0.9}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        # problem_ratio=0 → 0 points
        assert result.score < 10
        assert result.details["solution_count"] == 10

    async def test_all_other(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "other", "score": 0.8}] * 10

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10), following=[])
        result = await analyzer.analyze(data)

        assert result.score < 10
        assert result.details["other_count"] == 10

    async def test_topic_shift_detected(self, mock_pipeline):
        """Alternating problem/solution should trigger shift detection."""
        analyzer, pipe = mock_pipeline

        # Alternating pattern: problem, solution, problem, solution...
        pipe.return_value = [
            {"label": "problem" if i % 2 == 0 else "solution", "score": 0.9}
            for i in range(20)
        ]

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(20), following=[])
        result = await analyzer.analyze(data)

        assert result.details["shift_score"] > 0

    async def test_consistent_topic_no_shift(self, mock_pipeline):
        """Consistent topic should have low shift score."""
        analyzer, pipe = mock_pipeline

        pipe.return_value = [{"label": "problem", "score": 0.9}] * 20

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(20), following=[])
        result = await analyzer.analyze(data)

        assert result.details["shift_score"] == 0.0

    async def test_no_tweets(self, mock_pipeline):
        analyzer, pipe = mock_pipeline

        data = AnalysisInput(profile=PROFILE, tweets=[], following=[])
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1
        pipe.assert_not_called()

    async def test_few_tweets_no_shift(self, mock_pipeline):
        """Too few tweets for shift analysis."""
        analyzer, pipe = mock_pipeline
        pipe.return_value = [
            {"label": "problem", "score": 0.9},
            {"label": "solution", "score": 0.9},
            {"label": "problem", "score": 0.9},
        ]

        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(3), following=[])
        result = await analyzer.analyze(data)

        # shift_score should be 0 because < WINDOW_SIZE * 2
        assert result.details["shift_score"] == 0.0

    async def test_confidence_with_long_span(self, mock_pipeline):
        analyzer, pipe = mock_pipeline
        pipe.return_value = [{"label": "other", "score": 0.9}] * 20

        data = AnalysisInput(
            profile=PROFILE,
            tweets=_make_tweets(20, span_days=60),
            following=[],
        )
        result = await analyzer.analyze(data)

        assert result.confidence >= 0.85

    async def test_name_and_version(self, mock_pipeline):
        analyzer, _ = mock_pipeline
        assert analyzer.name == "political_shift"
        assert analyzer.version == "1.0.0"
