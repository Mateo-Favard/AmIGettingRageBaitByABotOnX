"""Tests for the model ensemble strategy (mocked HF pipelines)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.domain.models.twitter import TweetData
from app.infrastructure.ml.analyzers.ai_content.model_ensemble import (
    ENSEMBLE_MODELS,
    ModelEnsembleStrategy,
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


def _make_strategy(
    pipe_results: list[list[dict[str, object]]],
) -> ModelEnsembleStrategy:
    """Create a ModelEnsembleStrategy with mocked pipelines."""
    strategy = ModelEnsembleStrategy.__new__(ModelEnsembleStrategy)
    strategy._pipelines = []

    for i, results in enumerate(pipe_results):
        spec = ENSEMBLE_MODELS[i] if i < len(ENSEMBLE_MODELS) else ENSEMBLE_MODELS[0]
        mock_pipe = MagicMock()
        mock_pipe.return_value = results
        strategy._pipelines.append((spec, mock_pipe))

    return strategy


class TestModelEnsembleStrategy:
    async def test_name(self):
        strategy = _make_strategy([[]])
        assert strategy.name == "model_ensemble"

    async def test_both_models_agree_ai(self):
        """Both models detect AI -> high score."""
        n = 5
        strategy = _make_strategy(
            [
                [{"label": "LABEL_1", "score": 0.95}] * n,
                [{"label": "ChatGPT", "score": 0.90}] * n,
            ]
        )
        texts = [f"text {i}" for i in range(n)]
        tweets = _make_tweets(n)
        result = await strategy.detect(texts, tweets)

        assert result.score > 0.8
        assert result.confidence > 0.5

    async def test_both_models_agree_human(self):
        """Both models detect human -> low score."""
        n = 5
        strategy = _make_strategy(
            [
                [{"label": "LABEL_0", "score": 0.95}] * n,
                [{"label": "Human", "score": 0.90}] * n,
            ]
        )
        texts = [f"text {i}" for i in range(n)]
        tweets = _make_tweets(n)
        result = await strategy.detect(texts, tweets)

        assert result.score < 0.2

    async def test_models_disagree(self):
        """Models disagree -> moderate score, lower confidence."""
        n = 5
        strategy = _make_strategy(
            [
                [{"label": "LABEL_1", "score": 0.90}] * n,
                [{"label": "Human", "score": 0.90}] * n,
            ]
        )
        texts = [f"text {i}" for i in range(n)]
        tweets = _make_tweets(n)
        result = await strategy.detect(texts, tweets)

        assert 0.3 < result.score < 0.7

    async def test_single_model_graceful(self):
        """One model fails -> still works with remaining model."""
        n = 5
        failing_pipe = MagicMock(side_effect=RuntimeError("model error"))

        strategy = ModelEnsembleStrategy.__new__(ModelEnsembleStrategy)
        good_pipe = MagicMock()
        good_pipe.return_value = [{"label": "LABEL_1", "score": 0.85}] * n

        strategy._pipelines = [
            (ENSEMBLE_MODELS[0], good_pipe),
            (ENSEMBLE_MODELS[1], failing_pipe),
        ]

        texts = [f"text {i}" for i in range(n)]
        tweets = _make_tweets(n)
        result = await strategy.detect(texts, tweets)

        assert result.score > 0.5
        assert result.details["models_used"] == 2

    async def test_empty_texts(self):
        strategy = _make_strategy([[]])
        result = await strategy.detect([], [])
        assert result.score == 0.0

    async def test_health_check_success(self):
        strategy = _make_strategy(
            [
                [{"label": "LABEL_1", "score": 0.5}],
            ]
        )
        assert await strategy.health_check() is True

    async def test_confidence_increases_with_tweets(self):
        strategy_5 = _make_strategy(
            [
                [{"label": "LABEL_1", "score": 0.8}] * 5,
            ]
        )
        result_5 = await strategy_5.detect(
            [f"t {i}" for i in range(5)], _make_tweets(5)
        )

        strategy_20 = _make_strategy(
            [
                [{"label": "LABEL_1", "score": 0.8}] * 20,
            ]
        )
        result_20 = await strategy_20.detect(
            [f"t {i}" for i in range(20)], _make_tweets(20)
        )

        assert result_20.confidence > result_5.confidence
