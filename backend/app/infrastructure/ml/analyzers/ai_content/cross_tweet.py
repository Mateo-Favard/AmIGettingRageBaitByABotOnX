from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.infrastructure.ml.analyzers.ai_content.base import (
    AIDetectionStrategy,
    StrategyResult,
)

if TYPE_CHECKING:
    from app.domain.models.twitter import TweetData

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIR = "sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"


class CrossTweetStrategy(AIDetectionStrategy):
    """Cross-tweet pattern analysis using sentence embeddings."""

    def __init__(self, models_path: str = "models") -> None:
        from sentence_transformers import SentenceTransformer

        models = Path(models_path)
        model_path = models / EMBEDDING_DIR
        model_id = str(model_path) if model_path.exists() else EMBEDDING_MODEL

        self._model: Any = SentenceTransformer(model_id)

    @property
    def name(self) -> str:
        return "cross_tweet"

    async def detect(
        self,
        texts: list[str],
        tweets: list[TweetData],
    ) -> StrategyResult:
        if len(texts) < 3:
            return StrategyResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "insufficient_tweets", "count": len(texts)},
            )

        import numpy as np

        embeddings = await asyncio.to_thread(
            self._model.encode, texts, show_progress_bar=False
        )
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-10)
        normalized = embeddings / norms
        sim_matrix = np.dot(normalized, normalized.T)

        n = len(texts)

        # Signal 1: Auto-similarity (mean of upper triangle)
        upper_triangle: list[float] = []
        for i in range(n):
            for j in range(i + 1, n):
                upper_triangle.append(float(sim_matrix[i][j]))

        auto_similarity = (
            sum(upper_triangle) / len(upper_triangle) if upper_triangle else 0.0
        )

        # Signal 2: Template detection — high similarity pairs
        cluster_threshold = 0.85
        high_sim_count = sum(1 for s in upper_triangle if s > cluster_threshold)
        total_pairs = len(upper_triangle)
        template_ratio = high_sim_count / total_pairs if total_pairs > 0 else 0.0

        # Normalize to 0-1
        sim_score = min(1.0, max(0.0, (auto_similarity - 0.25) / 0.45))
        template_score = min(1.0, template_ratio * 5)

        combined = sim_score * 0.6 + template_score * 0.4
        combined = min(1.0, max(0.0, combined))

        confidence = 0.3 if n < 5 else 0.5 if n < 10 else 0.7

        return StrategyResult(
            score=round(combined, 4),
            confidence=round(confidence, 2),
            details={
                "auto_similarity": round(auto_similarity, 4),
                "template_ratio": round(template_ratio, 4),
                "high_similarity_pairs": high_sim_count,
                "total_pairs": total_pairs,
                "tweets_analyzed": n,
            },
        )

    async def health_check(self) -> bool:
        try:
            result = self._model.encode(["Test"])
            return result is not None and len(result) > 0
        except Exception:
            return False
