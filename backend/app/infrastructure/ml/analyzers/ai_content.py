from __future__ import annotations

import logging
import statistics
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.domain.interfaces.analyzer import AnalyzerInterface, AnalyzerResult

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import AnalysisInput

logger = logging.getLogger(__name__)

MODEL_REPO = "almanach/camemberta-chatgptdetect-noisy"
MODEL_DIR = "almanach--camemberta-chatgptdetect-noisy"


class AIContentAnalyzer(AnalyzerInterface):
    """Detects AI-generated text using a French-native CamemBERTa model.

    Uses almanach/camemberta-chatgptdetect-noisy trained directly on French
    text — no translation step needed, avoiding translation bias.
    """

    def __init__(self, models_path: str = "models") -> None:
        from transformers import pipeline as hf_pipeline

        models = Path(models_path)
        model_path = models / MODEL_DIR
        model_id = str(model_path) if model_path.exists() else MODEL_REPO

        self._pipeline: Any = hf_pipeline(
            "text-classification",
            model=model_id,
            tokenizer=model_id,
            truncation=True,
            max_length=512,
        )

    @property
    def name(self) -> str:
        return "ai_content"

    @property
    def version(self) -> str:
        return "2.0.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        tweets = data.tweets
        if not tweets:
            return AnalyzerResult(
                score=0.0, confidence=0.1, details={"reason": "no_tweets"}
            )

        texts = [t.content for t in tweets]
        ai_probabilities = self._detect_batch(texts)

        if not ai_probabilities:
            return AnalyzerResult(
                score=0.0, confidence=0.1, details={"reason": "detection_failed"}
            )

        mean_prob = statistics.mean(ai_probabilities)
        score = min(100.0, max(0.0, round(mean_prob * 100, 1)))

        confidence = self._compute_confidence(len(ai_probabilities), ai_probabilities)

        return AnalyzerResult(
            score=score,
            confidence=confidence,
            details={
                "mean_ai_probability": round(mean_prob, 4),
                "tweets_analyzed": len(ai_probabilities),
                "max_ai_probability": round(max(ai_probabilities), 4),
                "min_ai_probability": round(min(ai_probabilities), 4),
            },
        )

    async def health_check(self) -> bool:
        try:
            result = self._pipeline("Ceci est un test.")
            return result is not None and len(result) > 0
        except Exception:
            return False

    def _detect_batch(self, texts: list[str]) -> list[float]:
        """Run AI detection on French texts. Returns probability of AI."""
        results = self._pipeline(texts, batch_size=16)
        probabilities: list[float] = []

        for r in results:
            label = r["label"]
            prob = r["score"]
            # Model outputs "LABEL_1" (AI) or "LABEL_0" (Human)
            if label == "LABEL_1":
                probabilities.append(prob)
            else:
                probabilities.append(1.0 - prob)

        return probabilities

    @staticmethod
    def _compute_confidence(count: int, probabilities: list[float]) -> float:
        """Confidence based on tweet count and result consistency."""
        if count >= 20:
            base = 0.9
        elif count >= 10:
            base = 0.7
        elif count >= 5:
            base = 0.5
        else:
            base = 0.3

        if len(probabilities) >= 2:
            stdev = statistics.stdev(probabilities)
            consistency_bonus = max(0.0, (0.5 - stdev) * 0.2)
            base = min(0.95, base + consistency_bonus)

        return round(base, 2)
