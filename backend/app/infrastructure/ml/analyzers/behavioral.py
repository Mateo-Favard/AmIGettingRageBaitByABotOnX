from __future__ import annotations

import statistics
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.domain.interfaces.analyzer import AnalyzerInterface, AnalyzerResult

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import AnalysisInput


class BehavioralAnalyzer(AnalyzerInterface):
    """Detects suspicious behavioral patterns using pure heuristics."""

    @property
    def name(self) -> str:
        return "behavioral"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        signals: list[float] = []
        computable = 0
        total_signals = 5

        # 1. Follower/following ratio
        ratio_score = self._follower_ratio_score(data)
        signals.append(ratio_score)
        computable += 1

        # 2. Account age vs post volume
        age_score = self._age_vs_volume_score(data)
        if age_score is not None:
            signals.append(age_score)
            computable += 1

        # 3. Publishing regularity
        regularity_score = self._regularity_score(data)
        if regularity_score is not None:
            signals.append(regularity_score)
            computable += 1

        # 4. 24/7 posting patterns
        hours_score = self._posting_hours_score(data)
        if hours_score is not None:
            signals.append(hours_score)
            computable += 1

        # 5. Engagement rate
        engagement_score = self._engagement_score(data)
        if engagement_score is not None:
            signals.append(engagement_score)
            computable += 1

        score = statistics.mean(signals) if signals else 0.0
        confidence = computable / total_signals

        return AnalyzerResult(
            score=min(100.0, max(0.0, round(score, 1))),
            confidence=round(confidence, 2),
            details={
                "follower_ratio_score": ratio_score,
                "age_volume_score": age_score,
                "regularity_score": regularity_score,
                "posting_hours_score": hours_score,
                "engagement_score": engagement_score,
            },
        )

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def _follower_ratio_score(data: AnalysisInput) -> float:
        """High followers/following ratio is suspicious."""
        p = data.profile
        if p.following_count == 0:
            ratio = float(min(p.followers_count, 10000))
        else:
            ratio = p.followers_count / p.following_count

        if ratio <= 20:
            return 0.0
        if ratio >= 500:
            return 100.0
        return (ratio - 20) / (500 - 20) * 100.0

    @staticmethod
    def _age_vs_volume_score(data: AnalysisInput) -> float | None:
        """High tweets/day relative to account age is suspicious."""
        p = data.profile
        if p.account_created_at is None:
            return None

        now = datetime.now(tz=UTC)
        age_days = max(1, (now - p.account_created_at).days)
        tweets_per_day = p.tweets_count / age_days

        if tweets_per_day <= 20:
            return 0.0
        if tweets_per_day >= 100:
            return 100.0
        return (tweets_per_day - 20) / (100 - 20) * 100.0

    @staticmethod
    def _regularity_score(data: AnalysisInput) -> float | None:
        """Unnaturally regular posting intervals suggest automation."""
        tweets = data.tweets
        if len(tweets) < 3:
            return None

        sorted_tweets = sorted(tweets, key=lambda t: t.posted_at)
        intervals = [
            (
                sorted_tweets[i + 1].posted_at - sorted_tweets[i].posted_at
            ).total_seconds()
            for i in range(len(sorted_tweets) - 1)
        ]

        intervals = [i for i in intervals if i > 0]
        if len(intervals) < 2:
            return None

        mean_interval = statistics.mean(intervals)
        if mean_interval == 0:
            return 100.0

        std_dev = statistics.stdev(intervals)
        # Coefficient of variation: low = regular = suspicious
        cv = std_dev / mean_interval

        if cv >= 1.0:
            return 0.0  # High variance = human-like
        if cv <= 0.1:
            return 100.0  # Very regular = bot-like
        return max(0.0, (1.0 - cv) / 0.9 * 100.0)

    @staticmethod
    def _posting_hours_score(data: AnalysisInput) -> float | None:
        """Activity spread across many hours suggests non-human."""
        tweets = data.tweets
        if len(tweets) < 5:
            return None

        unique_hours = len({t.posted_at.hour for t in tweets})

        if unique_hours <= 12:
            return 0.0  # Normal human pattern
        if unique_hours >= 22:
            return 100.0  # Active almost all hours
        return (unique_hours - 12) / (22 - 12) * 100.0

    @staticmethod
    def _engagement_score(data: AnalysisInput) -> float | None:
        """Abnormal engagement rate vs follower count."""
        p = data.profile
        tweets = data.tweets
        if not tweets or p.followers_count == 0:
            return None

        total_engagement = sum(
            t.likes_count + t.retweets_count + t.replies_count for t in tweets
        )
        avg_engagement = total_engagement / len(tweets)
        engagement_rate = avg_engagement / p.followers_count

        # Very high engagement rate relative to followers is suspicious
        # Normal: 0.01-0.05, Suspicious: > 0.20
        if engagement_rate <= 0.05:
            return 0.0
        if engagement_rate >= 0.50:
            return 100.0
        return (engagement_rate - 0.05) / (0.50 - 0.05) * 100.0
