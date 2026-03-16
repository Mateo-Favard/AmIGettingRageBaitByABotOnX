from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from app.domain.interfaces.analyzer import AnalyzerInterface, AnalyzerResult
from app.infrastructure.ml.analyzers.ai_content.scoring import combine_strategies

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import AnalysisInput
    from app.domain.models.twitter import TweetData
    from app.infrastructure.ml.analyzers.ai_content.base import (
        AIDetectionStrategy,
        StrategyResult,
    )

logger = logging.getLogger(__name__)


class AIContentAnalyzer(AnalyzerInterface):
    """Multi-strategy AI content detection sub-pipeline.

    Orchestrates model ensemble, statistical, and cross-tweet strategies
    in parallel, then combines results.
    """

    def __init__(
        self,
        models_path: str = "models",
        *,
        settings: object | None = None,
    ) -> None:
        self._strategies: list[AIDetectionStrategy] = []
        self._strategy_timeout: float = 45.0

        statistical_enabled = True
        cross_tweet_enabled = True

        if settings is not None:
            self._strategy_timeout = getattr(
                settings, "ai_content_strategy_timeout_seconds", 20.0
            )
            statistical_enabled = getattr(
                settings, "ai_content_statistical_enabled", True
            )
            cross_tweet_enabled = getattr(
                settings, "ai_content_cross_tweet_enabled", True
            )

        self._init_strategies(models_path, statistical_enabled, cross_tweet_enabled)

    def _init_strategies(
        self,
        models_path: str,
        statistical_enabled: bool,
        cross_tweet_enabled: bool,
    ) -> None:
        # Axe 1: Model ensemble
        try:
            from app.infrastructure.ml.analyzers.ai_content.model_ensemble import (
                ModelEnsembleStrategy,
            )

            self._strategies.append(ModelEnsembleStrategy(models_path=models_path))
        except Exception:
            logger.warning("ModelEnsembleStrategy not available")

        # Axe 2: Statistical (pure Python, always available)
        if statistical_enabled:
            try:
                from app.infrastructure.ml.analyzers.ai_content.statistical import (
                    StatisticalStrategy,
                )

                self._strategies.append(StatisticalStrategy())
            except Exception:
                logger.warning("StatisticalStrategy not available")

        # Axe 3: Cross-tweet (requires sentence-transformers)
        if cross_tweet_enabled:
            try:
                from app.infrastructure.ml.analyzers.ai_content.cross_tweet import (
                    CrossTweetStrategy,
                )

                self._strategies.append(CrossTweetStrategy(models_path=models_path))
            except Exception:
                logger.warning("CrossTweetStrategy not available")

        logger.info(
            "AIContentAnalyzer initialized with %d strategies: %s",
            len(self._strategies),
            [s.name for s in self._strategies],
        )

    @property
    def name(self) -> str:
        return "ai_content"

    @property
    def version(self) -> str:
        return "3.0.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        tweets = data.tweets
        if not tweets:
            return AnalyzerResult(
                score=0.0, confidence=0.1, details={"reason": "no_tweets"}
            )

        if not self._strategies:
            return AnalyzerResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "no_strategies_available"},
            )

        texts = [t.content for t in tweets]

        # Run strategies in parallel with individual timeouts
        results = await self._run_strategies(texts, tweets)

        if not results:
            return AnalyzerResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "all_strategies_failed"},
            )

        score, confidence, details = combine_strategies(results)
        return AnalyzerResult(score=score, confidence=confidence, details=details)

    async def _run_strategies(
        self,
        texts: list[str],
        tweets: list[TweetData],
    ) -> dict[str, StrategyResult]:
        """Execute all strategies in parallel with timeout."""

        async def _run_one(
            strategy: AIDetectionStrategy,
        ) -> tuple[str, StrategyResult | None]:
            return await self._run_single_strategy_tuple(strategy, texts, tweets)

        tasks = [_run_one(s) for s in self._strategies]
        completed = await asyncio.gather(*tasks)

        results: dict[str, StrategyResult] = {}
        for name, result in completed:
            if result is not None:
                results[name] = result
        return results

    async def _run_single_strategy_tuple(
        self,
        strategy: AIDetectionStrategy,
        texts: list[str],
        tweets: list[TweetData],
    ) -> tuple[str, StrategyResult | None]:
        result = await self._run_single_strategy(strategy, texts, tweets)
        return strategy.name, result

    async def _run_single_strategy(
        self,
        strategy: AIDetectionStrategy,
        texts: list[str],
        tweets: list[TweetData],
    ) -> StrategyResult | None:
        try:
            result = await asyncio.wait_for(
                strategy.detect(texts, tweets),
                timeout=self._strategy_timeout,
            )
            logger.info(
                "Strategy %s completed: score=%.3f confidence=%.2f",
                strategy.name,
                result.score,
                result.confidence,
            )
            return result
        except TimeoutError:
            logger.warning(
                "Strategy %s timed out after %.1fs",
                strategy.name,
                self._strategy_timeout,
            )
            return None
        except Exception:
            logger.exception("Strategy %s failed", strategy.name)
            return None

    async def health_check(self) -> bool:
        if not self._strategies:
            return False
        for strategy in self._strategies:
            try:
                if await asyncio.wait_for(strategy.health_check(), timeout=5.0):
                    return True
            except Exception:
                logger.warning("Strategy %s health check failed", strategy.name)
                continue
        return False
