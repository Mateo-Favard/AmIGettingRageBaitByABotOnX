from __future__ import annotations

import asyncio
import logging
import statistics as stats_module
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.infrastructure.ml.analyzers.ai_content.base import (
    AIDetectionStrategy,
    StrategyResult,
)

if TYPE_CHECKING:
    from app.domain.models.twitter import TweetData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EnsembleModelSpec:
    repo_id: str
    dir_name: str
    weight: float
    ai_labels: frozenset[str]


ENSEMBLE_MODELS: list[EnsembleModelSpec] = [
    EnsembleModelSpec(
        repo_id="almanach/camemberta-chatgptdetect-noisy",
        dir_name="almanach--camemberta-chatgptdetect-noisy",
        weight=0.5,
        ai_labels=frozenset({"LABEL_1"}),
    ),
    EnsembleModelSpec(
        repo_id="Hello-SimpleAI/chatgpt-detector-roberta",
        dir_name="Hello-SimpleAI--chatgpt-detector-roberta",
        weight=0.5,
        ai_labels=frozenset({"ChatGPT", "LABEL_0"}),
    ),
]


class ModelEnsembleStrategy(AIDetectionStrategy):
    """Ensemble of HuggingFace text-classification models for AI detection."""

    def __init__(self, models_path: str = "models") -> None:
        from transformers import pipeline as hf_pipeline

        self._pipelines: list[tuple[EnsembleModelSpec, Any]] = []
        models = Path(models_path)

        for spec in ENSEMBLE_MODELS:
            model_path = models / spec.dir_name
            model_id = str(model_path) if model_path.exists() else spec.repo_id
            try:
                pipe = hf_pipeline(
                    "text-classification",
                    model=model_id,
                    tokenizer=model_id,
                    truncation=True,
                    max_length=512,
                )
                self._pipelines.append((spec, pipe))
                logger.info("Loaded model: %s", spec.repo_id)
            except Exception:
                logger.warning("Failed to load model: %s", spec.repo_id)

        if not self._pipelines:
            msg = "No models could be loaded for ModelEnsembleStrategy"
            raise RuntimeError(msg)

    @property
    def name(self) -> str:
        return "model_ensemble"

    async def detect(
        self,
        texts: list[str],
        tweets: list[TweetData],
    ) -> StrategyResult:
        if not texts:
            return StrategyResult(
                score=0.0, confidence=0.1, details={"reason": "no_texts"}
            )

        # Run all models in parallel threads
        tasks = [
            asyncio.to_thread(self._run_model, pipe, texts, spec.ai_labels)
            for spec, pipe in self._pipelines
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        model_probabilities: list[list[float]] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning("Model inference failed: %s", result)
                continue
            if result:
                model_probabilities.append(result)

        if not model_probabilities:
            return StrategyResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "all_models_failed"},
            )

        n_tweets = len(texts)
        combined_probs: list[float] = []
        for i in range(n_tweets):
            weighted_sum = 0.0
            total_weight = 0.0
            for j, (spec, _) in enumerate(self._pipelines):
                if j < len(model_probabilities) and i < len(model_probabilities[j]):
                    weighted_sum += model_probabilities[j][i] * spec.weight
                    total_weight += spec.weight
            if total_weight > 0:
                combined_probs.append(weighted_sum / total_weight)

        if not combined_probs:
            return StrategyResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "combination_failed"},
            )

        mean_prob = stats_module.mean(combined_probs)
        confidence = self._compute_confidence(
            n_tweets=len(combined_probs),
            model_probabilities=model_probabilities,
        )

        return StrategyResult(
            score=round(mean_prob, 4),
            confidence=confidence,
            details={
                "mean_ai_probability": round(mean_prob, 4),
                "tweets_analyzed": len(combined_probs),
                "max_ai_probability": round(max(combined_probs), 4),
                "min_ai_probability": round(min(combined_probs), 4),
                "models_used": len(self._pipelines),
            },
        )

    async def health_check(self) -> bool:
        if not self._pipelines:
            return False
        try:
            _, pipe = self._pipelines[0]
            result = pipe("Ceci est un test.")
            return result is not None and len(result) > 0
        except Exception:
            return False

    @staticmethod
    def _run_model(
        pipe: Any,
        texts: list[str],
        ai_labels: frozenset[str],
    ) -> list[float]:
        """Run a single model and extract AI probabilities."""
        try:
            results = pipe(texts, batch_size=16)
        except Exception:
            logger.exception("Model inference failed")
            return []

        probabilities: list[float] = []
        for r in results:
            label = r["label"]
            prob = r["score"]
            if label in ai_labels:
                probabilities.append(prob)
            else:
                probabilities.append(1.0 - prob)
        return probabilities

    def _compute_confidence(
        self,
        n_tweets: int,
        model_probabilities: list[list[float]],
    ) -> float:
        """Confidence based on tweet count and inter-model agreement."""
        if n_tweets >= 20:
            base = 0.9
        elif n_tweets >= 10:
            base = 0.7
        elif n_tweets >= 5:
            base = 0.5
        else:
            base = 0.3

        if len(model_probabilities) >= 2:
            disagreements: list[float] = []
            n = min(len(probs) for probs in model_probabilities)
            for i in range(n):
                values = [probs[i] for probs in model_probabilities]
                disagreements.append(max(values) - min(values))

            if disagreements:
                mean_disagreement = stats_module.mean(disagreements)
                agreement_factor = max(0.0, (0.3 - mean_disagreement) * 0.3)
                base = min(0.95, base + agreement_factor)

        return round(base, 2)
