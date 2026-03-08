from __future__ import annotations

import logging
import statistics
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.domain.interfaces.analyzer import AnalyzerInterface, AnalyzerResult

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import AnalysisInput
    from app.domain.models.twitter import TweetData

logger = logging.getLogger(__name__)

MODEL_REPO = "mazancourt/politics-sentence-classifier"
MODEL_DIR_NAME = "mazancourt--politics-sentence-classifier"

# Rolling window size for temporal analysis
WINDOW_SIZE = 5


class OpportunismAnalyzer(AnalyzerInterface):
    """Detects opportunistic rage-bait patterns via three signals:
    - Problem-framing ratio (CamemBERT classifier)
    - Temporal topic shifts (rolling window variance)
    - Trend-jacking (tweets matching current trending topics)
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
            "text-classification",
            model=model_id,
            tokenizer=model_id,
            truncation=True,
            max_length=280,
        )

    @property
    def name(self) -> str:
        return "opportunism"

    @property
    def version(self) -> str:
        return "2.0.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        tweets = data.tweets
        if not tweets:
            return AnalyzerResult(
                score=0.0, confidence=0.1, details={"reason": "no_tweets"}
            )

        # Sort tweets chronologically
        sorted_tweets = sorted(tweets, key=lambda t: t.posted_at)
        texts = [t.content for t in sorted_tweets]

        # Classify each tweet
        results = self._pipeline(texts, batch_size=16)

        labels = [r["label"].lower() for r in results]
        total = len(labels)

        # Count categories
        problem_count = sum(
            1 for lbl in labels if "problem" in lbl or "problème" in lbl
        )
        solution_count = sum(1 for lbl in labels if "solution" in lbl)
        other_count = total - problem_count - solution_count

        problem_ratio = problem_count / total

        # Signal 1: Problem ratio (max 40 points)
        problem_score = problem_ratio * 40

        # Signal 2: Temporal shift analysis (max 30 points)
        shift_score = self._compute_shift_score(labels)

        # Signal 3: Trend-jacking (max 30 points)
        trend_score = self._compute_trend_score(texts, data.trends)

        score = min(100.0, max(0.0, round(problem_score + shift_score + trend_score, 1)))
        confidence = self._compute_confidence(total, sorted_tweets)

        return AnalyzerResult(
            score=score,
            confidence=confidence,
            details={
                "problem_count": problem_count,
                "solution_count": solution_count,
                "other_count": other_count,
                "total_tweets": total,
                "problem_ratio": round(problem_ratio, 3),
                "shift_score": round(shift_score, 1),
                "trend_score": round(trend_score, 1),
                "trends_matched": self._find_matched_trends(texts, data.trends),
            },
        )

    async def health_check(self) -> bool:
        try:
            result = self._pipeline("La France va mal.")
            return result is not None and len(result) > 0
        except Exception:
            return False

    @staticmethod
    def _compute_shift_score(labels: list[str]) -> float:
        """Detect topic shifts using rolling window analysis.

        High variance in problem ratio across windows = opportunistic shifting.
        """
        if len(labels) < WINDOW_SIZE * 2:
            return 0.0

        # Compute problem ratio per rolling window
        window_ratios: list[float] = []
        for i in range(len(labels) - WINDOW_SIZE + 1):
            window = labels[i : i + WINDOW_SIZE]
            problem_in_window = sum(
                1 for lbl in window if "problem" in lbl or "problème" in lbl
            )
            window_ratios.append(problem_in_window / WINDOW_SIZE)

        if len(window_ratios) < 2:
            return 0.0

        # High variance = frequent topic shifts = suspicious
        variance = statistics.variance(window_ratios)
        # Scale: variance of 0.25 (max for binary) -> 30 points
        return min(30.0, variance * 120.0)

    @staticmethod
    def _compute_trend_score(texts: list[str], trends: list[str]) -> float:
        """Detect trend-jacking: tweets that match current trending topics.

        A high proportion of tweets mentioning trends suggests the account
        is opportunistically jumping on popular topics to maximize reach.
        """
        if not trends or not texts:
            return 0.0

        trends_lower = [t.lower() for t in trends]
        matching_tweets = 0
        for text in texts:
            text_lower = text.lower()
            if any(trend in text_lower for trend in trends_lower):
                matching_tweets += 1

        ratio = matching_tweets / len(texts)
        # 50%+ tweets on trending topics = max score
        return min(30.0, ratio * 60.0)

    @staticmethod
    def _find_matched_trends(texts: list[str], trends: list[str]) -> list[str]:
        """Return which trends were found in the tweets."""
        if not trends or not texts:
            return []
        matched: list[str] = []
        all_text = " ".join(t.lower() for t in texts)
        for trend in trends:
            if trend.lower() in all_text:
                matched.append(trend)
        return matched

    @staticmethod
    def _compute_confidence(tweet_count: int, sorted_tweets: list[TweetData]) -> float:
        """Confidence based on count and temporal span."""
        # Base confidence from tweet count
        if tweet_count >= 20:
            base = 0.85
        elif tweet_count >= 10:
            base = 0.6
        elif tweet_count >= 5:
            base = 0.4
        else:
            return 0.2

        # Bonus for temporal span (more days covered = better analysis)
        if len(sorted_tweets) >= 2:
            span_days = (sorted_tweets[-1].posted_at - sorted_tweets[0].posted_at).days
            if span_days >= 30:
                base = min(0.95, base + 0.1)
            elif span_days >= 7:
                base = min(0.95, base + 0.05)

        return round(base, 2)
