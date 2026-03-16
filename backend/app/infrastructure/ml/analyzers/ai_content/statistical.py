from __future__ import annotations

import logging
import math
import re
import statistics as stats_module
from collections import Counter
from typing import TYPE_CHECKING

from app.infrastructure.ml.analyzers.ai_content.base import (
    AIDetectionStrategy,
    StrategyResult,
)

if TYPE_CHECKING:
    from app.domain.models.twitter import TweetData

logger = logging.getLogger(__name__)

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]*")
_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


class StatisticalStrategy(AIDetectionStrategy):
    """Pure-Python statistical/linguistic features for AI detection."""

    @property
    def name(self) -> str:
        return "statistical"

    async def detect(
        self,
        texts: list[str],
        tweets: list[TweetData],
    ) -> StrategyResult:
        if not texts:
            return StrategyResult(
                score=0.0, confidence=0.1, details={"reason": "no_texts"}
            )

        combined = " ".join(texts)
        tokens = _WORD_RE.findall(combined.lower())

        if len(tokens) < 10:
            return StrategyResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "insufficient_tokens"},
            )

        signals = {
            "ttr": self._type_token_ratio(tokens),
            "sentence_uniformity": self._sentence_uniformity(texts),
            "punctuation_density": self._punctuation_density(combined),
            "burstiness": self._burstiness(tokens),
            "char_entropy": self._char_entropy(combined),
        }

        weights = {
            "ttr": 0.20,
            "sentence_uniformity": 0.25,
            "punctuation_density": 0.15,
            "burstiness": 0.20,
            "char_entropy": 0.20,
        }
        score = sum(signals[k] * weights[k] for k in signals)
        score = min(1.0, max(0.0, score))

        confidence = 0.15 if len(texts) < 5 else 0.5 if len(texts) < 10 else 0.7

        return StrategyResult(
            score=round(score, 4),
            confidence=round(confidence, 2),
            details={k: round(v, 4) for k, v in signals.items()},
        )

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def _type_token_ratio(tokens: list[str]) -> float:
        """High TTR = diverse vocabulary. AI tends higher than conversational."""
        if not tokens:
            return 0.0
        ttr = len(set(tokens)) / len(tokens)
        return min(1.0, max(0.0, (ttr - 0.3) / 0.5))

    @staticmethod
    def _sentence_uniformity(texts: list[str]) -> float:
        """AI produces more uniform sentence lengths."""
        all_sentences: list[str] = []
        for text in texts:
            sentences = [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]
            all_sentences.extend(sentences)

        if len(all_sentences) < 3:
            return 0.0

        lengths = [len(s.split()) for s in all_sentences]
        mean_len = stats_module.mean(lengths)
        if mean_len == 0:
            return 0.0

        stdev = stats_module.stdev(lengths)
        cv = stdev / mean_len
        return min(1.0, max(0.0, 1.0 - (cv - 0.2) / 0.7))

    @staticmethod
    def _punctuation_density(text: str) -> float:
        """AI has distinctive punctuation patterns."""
        if not text:
            return 0.0
        punct_count = len(_PUNCT_RE.findall(text))
        total_chars = len(text)
        if total_chars == 0:
            return 0.0

        density = punct_count / total_chars
        if 0.04 <= density <= 0.08:
            return 0.7 + (0.3 * (1 - abs(density - 0.06) / 0.02))
        if density < 0.04:
            return max(0.0, density / 0.04 * 0.5)
        return max(0.0, 0.5 - (density - 0.08) / 0.1 * 0.5)

    @staticmethod
    def _burstiness(tokens: list[str]) -> float:
        """AI text is less bursty (more uniform word frequency distribution)."""
        if len(tokens) < 10:
            return 0.0
        freq = Counter(tokens)
        frequencies = list(freq.values())
        if len(frequencies) < 2:
            return 0.0

        mean_f = stats_module.mean(frequencies)
        if mean_f == 0:
            return 0.0

        stdev_f = stats_module.stdev(frequencies)
        cv = stdev_f / mean_f
        return min(1.0, max(0.0, 1.0 - cv / 3.0))

    @staticmethod
    def _char_entropy(text: str) -> float:
        """AI tends towards higher character entropy."""
        if not text:
            return 0.0
        freq = Counter(text.lower())
        total = len(text)
        entropy = -sum(
            (count / total) * math.log2(count / total)
            for count in freq.values()
            if count > 0
        )
        return min(1.0, max(0.0, (entropy - 4.0) / 1.5))
