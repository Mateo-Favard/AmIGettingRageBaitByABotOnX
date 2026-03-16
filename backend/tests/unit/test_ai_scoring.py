"""Tests for the AI content scoring module."""

from __future__ import annotations

import pytest

from app.infrastructure.ml.analyzers.ai_content.base import StrategyResult
from app.infrastructure.ml.analyzers.ai_content.scoring import (
    DEFAULT_STRATEGY_WEIGHTS,
    combine_strategies,
)


class TestCombineStrategies:
    def test_empty_results(self):
        score, confidence, details = combine_strategies({})
        assert score == 0.0
        assert confidence == 0.1
        assert details["reason"] == "no_strategy_results"

    def test_single_strategy(self):
        results = {
            "model_ensemble": StrategyResult(score=0.8, confidence=0.9),
        }
        score, confidence, details = combine_strategies(results)
        assert score == 80.0
        assert confidence == 0.9
        assert "model_ensemble" in details["strategies_used"]

    def test_multiple_strategies(self):
        results = {
            "model_ensemble": StrategyResult(score=0.8, confidence=0.9),
            "statistical": StrategyResult(score=0.6, confidence=0.7),
        }
        score, confidence, _details = combine_strategies(results)
        assert 0 < score < 100
        assert 0 < confidence <= 1

    def test_confidence_affects_weighting(self):
        # High-confidence high score + low-confidence low score
        results_high_conf = {
            "model_ensemble": StrategyResult(score=0.9, confidence=1.0),
            "statistical": StrategyResult(score=0.1, confidence=0.1),
        }
        score_high, _, _ = combine_strategies(results_high_conf)

        # Low-confidence high score + high-confidence low score
        results_low_conf = {
            "model_ensemble": StrategyResult(score=0.9, confidence=0.1),
            "statistical": StrategyResult(score=0.1, confidence=1.0),
        }
        score_low, _, _ = combine_strategies(results_low_conf)

        # The high-confidence version should have higher score
        assert score_high > score_low

    def test_renormalization_with_missing_strategy(self):
        # Only model_ensemble and statistical present (cross_tweet missing)
        results = {
            "model_ensemble": StrategyResult(score=1.0, confidence=1.0),
            "statistical": StrategyResult(score=0.0, confidence=1.0),
        }
        score, _, _ = combine_strategies(results)
        # Weights: 0.50 and 0.22. Score = (1.0 * 0.50) / (0.50 + 0.22) * 100
        expected = round(0.50 / 0.72 * 100, 1)
        assert score == expected

    def test_custom_weights(self):
        results = {
            "model_ensemble": StrategyResult(score=1.0, confidence=1.0),
            "statistical": StrategyResult(score=0.0, confidence=1.0),
        }
        equal_weights = {"model_ensemble": 0.5, "statistical": 0.5}
        score, _, _ = combine_strategies(results, weights=equal_weights)
        assert score == 50.0

    def test_zero_confidence_ignored(self):
        results = {
            "model_ensemble": StrategyResult(score=0.8, confidence=0.9),
            "statistical": StrategyResult(score=0.0, confidence=0.0),
        }
        score, _, _ = combine_strategies(results)
        # Statistical has 0 confidence → zero adjusted weight → effectively ignored
        assert score == 80.0

    def test_all_zero_confidence(self):
        results = {
            "model_ensemble": StrategyResult(score=0.8, confidence=0.0),
            "statistical": StrategyResult(score=0.5, confidence=0.0),
        }
        score, _confidence, details = combine_strategies(results)
        assert score == 0.0
        assert details["reason"] == "zero_total_weight"

    def test_details_contain_strategy_info(self):
        results = {
            "model_ensemble": StrategyResult(
                score=0.7, confidence=0.8, details={"models_used": 2}
            ),
        }
        _, _, details = combine_strategies(results)
        assert "strategies_used" in details
        assert "strategy_scores" in details
        assert "strategy_confidences" in details
        assert "model_ensemble_details" in details

    def test_score_clamped_to_0_100(self):
        # Even with unusual inputs, score should be in [0, 100]
        results = {
            "model_ensemble": StrategyResult(score=1.0, confidence=1.0),
        }
        score, _, _ = combine_strategies(results)
        assert 0 <= score <= 100

    def test_default_weights_sum(self):
        total = sum(DEFAULT_STRATEGY_WEIGHTS.values())
        assert total == pytest.approx(1.0)
