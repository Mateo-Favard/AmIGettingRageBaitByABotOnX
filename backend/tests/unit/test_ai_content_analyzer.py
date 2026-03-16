"""Tests for the AI content analyzer coordinator (mocked strategies)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.domain.interfaces.analyzer import AnalysisInput, AnalyzerResult
from app.domain.models.twitter import TweetData, TwitterProfile
from app.infrastructure.ml.analyzers.ai_content.base import (
    AIDetectionStrategy,
    StrategyResult,
)
from app.infrastructure.ml.analyzers.ai_content.coordinator import AIContentAnalyzer

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


class FakeStrategy(AIDetectionStrategy):
    def __init__(
        self,
        name: str = "fake",
        score: float = 0.5,
        confidence: float = 0.8,
    ) -> None:
        self._name = name
        self._score = score
        self._confidence = confidence

    @property
    def name(self) -> str:
        return self._name

    async def detect(self, texts, tweets) -> StrategyResult:
        return StrategyResult(
            score=self._score,
            confidence=self._confidence,
            details={"source": self._name},
        )

    async def health_check(self) -> bool:
        return True


class FailingStrategy(AIDetectionStrategy):
    @property
    def name(self) -> str:
        return "failing"

    async def detect(self, texts, tweets) -> StrategyResult:
        msg = "Intentional failure"
        raise RuntimeError(msg)

    async def health_check(self) -> bool:
        return False


class SlowStrategy(AIDetectionStrategy):
    @property
    def name(self) -> str:
        return "slow"

    async def detect(self, texts, tweets) -> StrategyResult:
        await asyncio.sleep(60)
        return StrategyResult(score=0.0, confidence=0.0)

    async def health_check(self) -> bool:
        return True


def _make_analyzer(strategies: list[AIDetectionStrategy]) -> AIContentAnalyzer:
    """Create coordinator with pre-built strategies, bypassing model loading."""
    analyzer = AIContentAnalyzer.__new__(AIContentAnalyzer)
    analyzer._strategies = strategies
    analyzer._strategy_timeout = 20.0
    return analyzer


class TestAIContentAnalyzer:
    async def test_produces_valid_result(self):
        analyzer = _make_analyzer(
            [
                FakeStrategy("model_ensemble", score=0.8, confidence=0.9),
                FakeStrategy("statistical", score=0.6, confidence=0.7),
            ]
        )
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10))
        result = await analyzer.analyze(data)

        assert isinstance(result, AnalyzerResult)
        assert 0 <= result.score <= 100
        assert 0 <= result.confidence <= 1

    async def test_high_ai_score(self):
        analyzer = _make_analyzer(
            [
                FakeStrategy("model_ensemble", score=0.95, confidence=0.9),
                FakeStrategy("statistical", score=0.9, confidence=0.7),
            ]
        )
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10))
        result = await analyzer.analyze(data)

        assert result.score > 80

    async def test_low_ai_score(self):
        analyzer = _make_analyzer(
            [
                FakeStrategy("model_ensemble", score=0.05, confidence=0.9),
                FakeStrategy("statistical", score=0.1, confidence=0.7),
            ]
        )
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10))
        result = await analyzer.analyze(data)

        assert result.score < 20

    async def test_no_tweets(self):
        analyzer = _make_analyzer([FakeStrategy()])
        data = AnalysisInput(profile=PROFILE, tweets=[])
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.confidence == 0.1
        assert result.details["reason"] == "no_tweets"

    async def test_no_strategies(self):
        analyzer = _make_analyzer([])
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(5))
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.details["reason"] == "no_strategies_available"

    async def test_name_and_version(self):
        analyzer = _make_analyzer([])
        assert analyzer.name == "ai_content"
        assert analyzer.version == "3.0.0"

    async def test_graceful_degradation_one_fails(self):
        analyzer = _make_analyzer(
            [
                FakeStrategy("model_ensemble", score=0.7, confidence=0.9),
                FailingStrategy(),
            ]
        )
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10))
        result = await analyzer.analyze(data)

        assert result.score > 0
        assert "model_ensemble" in result.details.get("strategies_used", [])

    async def test_graceful_degradation_all_fail(self):
        analyzer = _make_analyzer([FailingStrategy()])
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10))
        result = await analyzer.analyze(data)

        assert result.score == 0.0
        assert result.details["reason"] == "all_strategies_failed"

    async def test_strategy_timeout(self):
        analyzer = _make_analyzer(
            [
                FakeStrategy("model_ensemble", score=0.7, confidence=0.9),
                SlowStrategy(),
            ]
        )
        analyzer._strategy_timeout = 0.1
        data = AnalysisInput(profile=PROFILE, tweets=_make_tweets(10))
        result = await analyzer.analyze(data)

        assert result.score > 0
        assert "model_ensemble" in result.details.get("strategies_used", [])

    async def test_health_check_with_healthy_strategy(self):
        analyzer = _make_analyzer([FakeStrategy()])
        assert await analyzer.health_check() is True

    async def test_health_check_with_no_strategies(self):
        analyzer = _make_analyzer([])
        assert await analyzer.health_check() is False

    async def test_health_check_with_failing_strategy(self):
        analyzer = _make_analyzer([FailingStrategy()])
        assert await analyzer.health_check() is False
