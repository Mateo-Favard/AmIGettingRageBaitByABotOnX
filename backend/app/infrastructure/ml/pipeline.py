from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import (
        AnalysisInput,
        AnalyzerInterface,
        AnalyzerResult,
    )

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS: dict[str, float] = {
    "ai_content": 0.25,
    "sentiment": 0.25,
    "behavioral": 0.20,
    "political_shift": 0.15,
    "network": 0.15,
}

DEFAULT_PER_ANALYZER_TIMEOUT: float = 30.0
DEFAULT_GLOBAL_TIMEOUT: float = 30.0


@dataclass(frozen=True)
class PipelineResult:
    """Aggregated result from all analyzers."""

    composite_score: float
    individual_scores: dict[str, float]
    confidences: dict[str, float]
    details: dict[str, dict[str, object]]
    model_versions: dict[str, str]
    failed_analyzers: list[str] = field(default_factory=list)


class MLPipeline:
    """Orchestrates multiple analyzers in parallel with fault tolerance."""

    def __init__(
        self,
        analyzers: list[AnalyzerInterface],
        weights: dict[str, float] | None = None,
        global_timeout: float = DEFAULT_GLOBAL_TIMEOUT,
        per_analyzer_timeout: float = DEFAULT_PER_ANALYZER_TIMEOUT,
    ) -> None:
        self._analyzers = analyzers
        self._weights = weights or DEFAULT_WEIGHTS
        self._global_timeout = global_timeout
        self._per_analyzer_timeout = per_analyzer_timeout

    async def _run_analyzer(
        self,
        analyzer: AnalyzerInterface,
        data: AnalysisInput,
    ) -> tuple[str, AnalyzerResult | None]:
        """Run a single analyzer with per-analyzer timeout."""
        name = analyzer.name
        try:
            result = await asyncio.wait_for(
                analyzer.analyze(data),
                timeout=self._per_analyzer_timeout,
            )
            logger.info(
                "Analyzer %s completed: score=%.1f confidence=%.2f",
                name,
                result.score,
                result.confidence,
            )
            return name, result
        except TimeoutError:
            logger.warning(
                "Analyzer %s timed out after %.1fs",
                name,
                self._per_analyzer_timeout,
            )
            return name, None
        except Exception:
            logger.exception("Analyzer %s failed", name)
            return name, None

    async def run(self, data: AnalysisInput) -> PipelineResult:
        """Execute all analyzers in parallel and compute composite score."""
        if not self._analyzers:
            return PipelineResult(
                composite_score=0.0,
                individual_scores={},
                confidences={},
                details={},
                model_versions={},
            )

        tasks = [self._run_analyzer(a, data) for a in self._analyzers]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=self._global_timeout,
            )
        except TimeoutError:
            logger.warning("Global pipeline timeout after %.1fs", self._global_timeout)
            results = [(a.name, None) for a in self._analyzers]

        individual_scores: dict[str, float] = {}
        confidences: dict[str, float] = {}
        details: dict[str, dict[str, object]] = {}
        model_versions: dict[str, str] = {}
        failed: list[str] = []

        for analyzer, (name, result) in zip(self._analyzers, results, strict=True):
            model_versions[name] = analyzer.version
            if result is None:
                failed.append(name)
            else:
                individual_scores[name] = result.score
                confidences[name] = result.confidence
                details[name] = dict(result.details)

        composite = self._compute_composite(individual_scores, confidences)

        return PipelineResult(
            composite_score=composite,
            individual_scores=individual_scores,
            confidences=confidences,
            details=details,
            model_versions=model_versions,
            failed_analyzers=failed,
        )

    def _compute_composite(
        self,
        scores: dict[str, float],
        confidences: dict[str, float],
    ) -> float:
        """Weighted average with confidence-adjusted renormalization."""
        if not scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for name, score in scores.items():
            weight = self._weights.get(name, 0.0)
            confidence = confidences.get(name, 1.0)
            adjusted_weight = weight * confidence
            weighted_sum += score * adjusted_weight
            total_weight += adjusted_weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 1)

    async def health_check(self) -> dict[str, bool]:
        """Check health of each registered analyzer."""
        results: dict[str, bool] = {}
        for analyzer in self._analyzers:
            try:
                healthy = await asyncio.wait_for(analyzer.health_check(), timeout=5.0)
                results[analyzer.name] = healthy
            except Exception:
                results[analyzer.name] = False
        return results
