"""Tests for the cross-tweet strategy (mocked embeddings model)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import numpy as np

from app.domain.models.twitter import TweetData
from app.infrastructure.ml.analyzers.ai_content.cross_tweet import CrossTweetStrategy


def _make_tweets(count: int) -> list[TweetData]:
    return [
        TweetData(
            twitter_id=str(i),
            content=f"Tweet {i}",
            posted_at=datetime(2024, 6, 1, tzinfo=UTC) + timedelta(hours=i),
        )
        for i in range(count)
    ]


def _make_strategy(embeddings: np.ndarray) -> CrossTweetStrategy:
    """Create strategy with a mocked embedding model."""
    strategy = CrossTweetStrategy.__new__(CrossTweetStrategy)
    mock_model = MagicMock()
    mock_model.encode.return_value = embeddings
    strategy._model = mock_model
    return strategy


class TestCrossTweetStrategy:
    async def test_name(self):
        strategy = _make_strategy(np.array([]))
        assert strategy.name == "cross_tweet"

    async def test_insufficient_tweets(self):
        strategy = _make_strategy(np.array([[1, 0], [0, 1]]))
        result = await strategy.detect(["a", "b"], _make_tweets(2))
        assert result.score == 0.0
        assert result.details["reason"] == "insufficient_tweets"

    async def test_identical_tweets_high_score(self):
        """All tweets with identical embeddings -> high similarity -> high score."""
        n = 10
        embeddings = np.tile([1.0, 0.0, 0.0, 0.0], (n, 1))
        strategy = _make_strategy(embeddings)

        texts = [f"text {i}" for i in range(n)]
        result = await strategy.detect(texts, _make_tweets(n))

        assert result.score > 0.8
        assert result.details["auto_similarity"] > 0.9

    async def test_diverse_tweets_low_score(self):
        """All tweets with orthogonal embeddings -> low similarity -> low score."""
        n = 5
        embeddings = np.eye(n)
        strategy = _make_strategy(embeddings)

        texts = [f"text {i}" for i in range(n)]
        result = await strategy.detect(texts, _make_tweets(n))

        assert result.score < 0.3
        assert result.details["auto_similarity"] < 0.1
        assert result.details["high_similarity_pairs"] == 0

    async def test_mixed_similarity(self):
        """Some tweets similar, some different -> moderate score."""
        n = 6
        embeddings = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.99, 0.1, 0.0],
                [0.98, 0.15, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.1, 0.0, 0.99],
            ]
        )
        strategy = _make_strategy(embeddings)

        texts = [f"text {i}" for i in range(n)]
        result = await strategy.detect(texts, _make_tweets(n))

        assert 0 < result.score < 1
        assert result.details["high_similarity_pairs"] > 0

    async def test_confidence_varies_with_count(self):
        """Confidence should increase with more tweets."""
        emb_small = np.random.default_rng(42).random((4, 10))
        strategy_small = _make_strategy(emb_small)
        result_small = await strategy_small.detect(
            [f"t{i}" for i in range(4)], _make_tweets(4)
        )

        emb_large = np.random.default_rng(42).random((15, 10))
        strategy_large = _make_strategy(emb_large)
        result_large = await strategy_large.detect(
            [f"t{i}" for i in range(15)], _make_tweets(15)
        )

        assert result_large.confidence > result_small.confidence

    async def test_template_detection(self):
        """Cluster of identical embeddings triggers template detection."""
        n = 8
        base = np.random.default_rng(123).random((1, 10))
        embeddings = np.vstack(
            [
                np.tile(base, (6, 1)),
                np.random.default_rng(456).random((2, 10)),
            ]
        )
        strategy = _make_strategy(embeddings)

        texts = [f"text {i}" for i in range(n)]
        result = await strategy.detect(texts, _make_tweets(n))

        assert result.details["high_similarity_pairs"] > 0
        assert result.details["template_ratio"] > 0

    async def test_health_check(self):
        strategy = _make_strategy(np.array([]))
        strategy._model.encode.return_value = np.array([[1, 2, 3]])
        assert await strategy.health_check() is True
