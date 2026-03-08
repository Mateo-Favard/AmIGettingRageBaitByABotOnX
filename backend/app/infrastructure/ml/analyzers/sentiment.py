from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.domain.interfaces.analyzer import AnalyzerInterface, AnalyzerResult

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import AnalysisInput

logger = logging.getLogger(__name__)

MODEL_REPO = "cardiffnlp/camembert-base-tweet-sentiment-fr"
MODEL_DIR_NAME = "cardiffnlp--camembert-base-tweet-sentiment-fr"


class SentimentAnalyzer(AnalyzerInterface):
    """Analyzes tweet sentiment to detect inflammatory rage-bait patterns.

    Uses CamemBERT fine-tuned on French tweets (3 classes: negative/neutral/positive).
    High proportion of negative content + absence of neutral = suspicious.
    """

    def __init__(self, models_path: str = "models") -> None:
        from transformers import pipeline as hf_pipeline

        model_path = Path(models_path) / MODEL_DIR_NAME
        if not model_path.exists():
            logger.info("Model not found locally, loading from hub: %s", MODEL_REPO)
            model_id: str = MODEL_REPO
        else:
            model_id = str(model_path)

        self._pipeline: Any = hf_pipeline(
            "sentiment-analysis",
            model=model_id,
            tokenizer=model_id,
            truncation=True,
            max_length=280,
        )

    @property
    def name(self) -> str:
        return "sentiment"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        tweets = data.tweets
        if not tweets:
            return AnalyzerResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "no_tweets"},
            )

        texts = [t.content for t in tweets]
        results = self._pipeline(texts, batch_size=16)

        negative_count = 0
        neutral_count = 0
        positive_count = 0

        for r in results:
            label = r["label"].lower()
            if "neg" in label:
                negative_count += 1
            elif "neu" in label:
                neutral_count += 1
            else:
                positive_count += 1

        total = len(results)
        negative_ratio = negative_count / total
        neutral_ratio = neutral_count / total

        # High negative + low neutral = rage bait pattern
        score = negative_ratio * 70 + (1 - neutral_ratio) * 30
        score = min(100.0, max(0.0, round(score, 1)))

        confidence = self._compute_confidence(total)

        return AnalyzerResult(
            score=score,
            confidence=confidence,
            details={
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "positive_count": positive_count,
                "total_tweets": total,
                "negative_ratio": round(negative_ratio, 3),
                "neutral_ratio": round(neutral_ratio, 3),
            },
        )

    async def health_check(self) -> bool:
        try:
            result = self._pipeline("Ceci est un test.")
            return result is not None and len(result) > 0
        except Exception:
            return False

    @staticmethod
    def _compute_confidence(tweet_count: int) -> float:
        if tweet_count >= 20:
            return 0.95
        if tweet_count >= 10:
            return 0.8
        if tweet_count >= 5:
            return 0.5
        return 0.2
