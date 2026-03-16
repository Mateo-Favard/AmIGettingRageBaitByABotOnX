"""Tests for the ML pipeline orchestrator and analyzer interface."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.interfaces.analyzer import (
    AnalysisInput,
    AnalyzerInterface,
    AnalyzerResult,
)
from app.domain.models.twitter import TweetData, TwitterProfile
from app.infrastructure.ml.pipeline import MLPipeline

# --- Test data ---

PROFILE = TwitterProfile(
    handle="test_user",
    display_name="Test User",
    bio="Test bio",
    followers_count=1000,
    following_count=500,
    tweets_count=200,
    account_created_at=datetime(2020, 1, 1, tzinfo=UTC),
)

TWEETS = [
    TweetData(
        twitter_id=str(i),
        content=f"Tweet number {i}",
        posted_at=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(hours=i),
        likes_count=10,
        retweets_count=5,
        replies_count=2,
    )
    for i in range(10)
]

INPUT = AnalysisInput(profile=PROFILE, tweets=TWEETS, trends=["a", "b", "c"])


# --- Fake analyzers ---


class FakeAnalyzer(AnalyzerInterface):
    def __init__(
        self,
        name: str = "fake",
        version: str = "1.0",
        score: float = 50.0,
        confidence: float = 0.9,
    ) -> None:
        self._name = name
        self._version = version
        self._score = score
        self._confidence = confidence

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        return AnalyzerResult(
            score=self._score,
            confidence=self._confidence,
            details={"source": self._name},
        )

    async def health_check(self) -> bool:
        return True


class FailingAnalyzer(AnalyzerInterface):
    @property
    def name(self) -> str:
        return "failing"

    @property
    def version(self) -> str:
        return "1.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        msg = "Intentional failure"
        raise RuntimeError(msg)

    async def health_check(self) -> bool:
        return False


class SlowAnalyzer(AnalyzerInterface):
    @property
    def name(self) -> str:
        return "slow"

    @property
    def version(self) -> str:
        return "1.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        await asyncio.sleep(60)
        return AnalyzerResult(score=0, confidence=0, details={})

    async def health_check(self) -> bool:
        return True


# --- AnalyzerResult validation tests ---


class TestAnalyzerResult:
    def test_valid_result(self):
        r = AnalyzerResult(score=50.0, confidence=0.8, details={"key": "val"})
        assert r.score == 50.0
        assert r.confidence == 0.8

    def test_score_too_high(self):
        with pytest.raises(ValueError, match="score must be 0-100"):
            AnalyzerResult(score=101, confidence=0.5)

    def test_score_too_low(self):
        with pytest.raises(ValueError, match="score must be 0-100"):
            AnalyzerResult(score=-1, confidence=0.5)

    def test_confidence_too_high(self):
        with pytest.raises(ValueError, match="confidence must be 0-1"):
            AnalyzerResult(score=50, confidence=1.5)

    def test_confidence_too_low(self):
        with pytest.raises(ValueError, match="confidence must be 0-1"):
            AnalyzerResult(score=50, confidence=-0.1)

    def test_boundary_values(self):
        r1 = AnalyzerResult(score=0, confidence=0)
        assert r1.score == 0
        r2 = AnalyzerResult(score=100, confidence=1)
        assert r2.score == 100


# --- Pipeline tests ---


class TestMLPipeline:
    async def test_all_analyzers_succeed(self):
        analyzers = [
            FakeAnalyzer(name="behavioral", score=60, confidence=0.9),
            FakeAnalyzer(name="sentiment", score=80, confidence=0.8),
        ]
        pipeline = MLPipeline(analyzers=analyzers)
        result = await pipeline.run(INPUT)

        assert result.composite_score > 0
        assert "behavioral" in result.individual_scores
        assert "sentiment" in result.individual_scores
        assert result.individual_scores["behavioral"] == 60
        assert result.individual_scores["sentiment"] == 80
        assert len(result.failed_analyzers) == 0

    async def test_one_analyzer_fails(self):
        analyzers = [
            FakeAnalyzer(name="behavioral", score=60, confidence=0.9),
            FailingAnalyzer(),
        ]
        pipeline = MLPipeline(analyzers=analyzers)
        result = await pipeline.run(INPUT)

        assert "behavioral" in result.individual_scores
        assert "failing" in result.failed_analyzers
        assert result.composite_score > 0  # Still computes from remaining

    async def test_analyzer_timeout(self):
        analyzers = [
            FakeAnalyzer(name="behavioral", score=60, confidence=0.9),
            SlowAnalyzer(),
        ]
        pipeline = MLPipeline(analyzers=analyzers, per_analyzer_timeout=0.1)
        result = await pipeline.run(INPUT)

        assert "behavioral" in result.individual_scores
        assert "slow" in result.failed_analyzers

    async def test_empty_pipeline(self):
        pipeline = MLPipeline(analyzers=[])
        result = await pipeline.run(INPUT)

        assert result.composite_score == 0.0
        assert result.individual_scores == {}
        assert result.failed_analyzers == []

    async def test_all_analyzers_fail(self):
        pipeline = MLPipeline(analyzers=[FailingAnalyzer()])
        result = await pipeline.run(INPUT)

        assert result.composite_score == 0.0
        assert "failing" in result.failed_analyzers

    async def test_model_versions_collected(self):
        analyzers = [
            FakeAnalyzer(name="behavioral", version="2.0"),
            FakeAnalyzer(name="sentiment", version="1.5"),
        ]
        pipeline = MLPipeline(analyzers=analyzers)
        result = await pipeline.run(INPUT)

        assert result.model_versions["behavioral"] == "2.0"
        assert result.model_versions["sentiment"] == "1.5"

    async def test_weighted_composite(self):
        # One analyzer scores 100, another scores 0, equal weights
        analyzers = [
            FakeAnalyzer(name="behavioral", score=100, confidence=1.0),
            FakeAnalyzer(name="sentiment", score=0, confidence=1.0),
        ]
        weights = {"behavioral": 0.5, "sentiment": 0.5}
        pipeline = MLPipeline(analyzers=analyzers, weights=weights)
        result = await pipeline.run(INPUT)

        assert result.composite_score == 50.0

    async def test_confidence_affects_composite(self):
        # High-confidence high score + low-confidence low score
        analyzers = [
            FakeAnalyzer(name="behavioral", score=100, confidence=1.0),
            FakeAnalyzer(name="sentiment", score=0, confidence=0.1),
        ]
        weights = {"behavioral": 0.5, "sentiment": 0.5}
        pipeline = MLPipeline(analyzers=analyzers, weights=weights)
        result = await pipeline.run(INPUT)

        # Composite should be weighted towards the high-confidence score
        assert result.composite_score > 80

    async def test_health_check(self):
        analyzers = [
            FakeAnalyzer(name="healthy"),
            FailingAnalyzer(),
        ]
        pipeline = MLPipeline(analyzers=analyzers)
        health = await pipeline.health_check()

        assert health["healthy"] is True
        assert health["failing"] is False

    async def test_global_timeout(self):
        analyzers = [SlowAnalyzer()]
        pipeline = MLPipeline(
            analyzers=analyzers,
            global_timeout=0.1,
            per_analyzer_timeout=60,
        )
        result = await pipeline.run(INPUT)

        assert "slow" in result.failed_analyzers
        assert result.composite_score == 0.0
