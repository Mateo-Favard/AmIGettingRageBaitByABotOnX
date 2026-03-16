from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.ml.analyzers.ai_content.base import StrategyResult

logger = logging.getLogger(__name__)

DEFAULT_STRATEGY_WEIGHTS: dict[str, float] = {
    "model_ensemble": 0.50,
    "cross_tweet": 0.28,
    "statistical": 0.22,
}


def combine_strategies(
    results: dict[str, StrategyResult],
    weights: dict[str, float] | None = None,
) -> tuple[float, float, dict[str, object]]:
    """Combine strategy results into a final (score, confidence, details) tuple.

    Returns score on 0-100 scale, confidence on 0-1 scale.
    """
    if not results:
        return 0.0, 0.1, {"reason": "no_strategy_results"}

    w = weights or DEFAULT_STRATEGY_WEIGHTS

    # Confidence-adjusted weighted average
    total_weight = 0.0
    weighted_sum = 0.0

    for name, result in results.items():
        base_weight = w.get(name, 0.0)
        adjusted_weight = base_weight * result.confidence
        weighted_sum += result.score * adjusted_weight
        total_weight += adjusted_weight

    if total_weight == 0:
        return 0.0, 0.1, {"reason": "zero_total_weight"}

    combined_score_01 = weighted_sum / total_weight
    score_100 = min(100.0, max(0.0, round(combined_score_01 * 100, 1)))

    # Overall confidence: weighted average of strategy confidences
    conf_sum = sum(w.get(name, 0.0) * r.confidence for name, r in results.items())
    conf_weight = sum(w.get(name, 0.0) for name in results)
    overall_confidence = round(conf_sum / conf_weight, 2) if conf_weight > 0 else 0.1

    details: dict[str, object] = {
        "strategies_used": list(results.keys()),
        "strategy_scores": {name: round(r.score, 4) for name, r in results.items()},
        "strategy_confidences": {
            name: round(r.confidence, 2) for name, r in results.items()
        },
    }
    for name, result in results.items():
        if result.details:
            details[f"{name}_details"] = dict(result.details)

    return score_100, overall_confidence, details
