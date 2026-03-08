from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.domain.interfaces.analyzer import AnalyzerInterface, AnalyzerResult

if TYPE_CHECKING:
    from app.domain.interfaces.analyzer import AnalysisInput
    from app.domain.interfaces.repositories import AccountRepositoryInterface

logger = logging.getLogger(__name__)

RAGE_BAIT_THRESHOLD = 70.0


class NetworkAnalyzer(AnalyzerInterface):
    """Analyzes social network connections for rage-bait patterns.

    Uses heuristics based on followed accounts already in the database.
    """

    def __init__(
        self,
        account_repo: AccountRepositoryInterface | None = None,
    ) -> None:
        self._repo = account_repo

    @property
    def name(self) -> str:
        return "network"

    @property
    def version(self) -> str:
        return "1.0.0"

    async def analyze(self, data: AnalysisInput) -> AnalyzerResult:
        following = data.following

        if not following or self._repo is None:
            return AnalyzerResult(
                score=0.0,
                confidence=0.1,
                details={"reason": "no_following_data_or_repo"},
            )

        # Check how many followed accounts are known rage-bait
        suspect_count = 0
        analyzed_count = 0
        suspect_handles: list[str] = []

        for handle in following:
            analysis = await self._repo.get_latest_analysis(handle)
            if analysis is not None:
                analyzed_count += 1
                if analysis.composite_score >= RAGE_BAIT_THRESHOLD:
                    suspect_count += 1
                    suspect_handles.append(handle)

        # Cold start: no analyzed accounts in DB
        if analyzed_count == 0:
            return AnalyzerResult(
                score=0.0,
                confidence=0.1,
                details={
                    "reason": "cold_start",
                    "total_following": len(following),
                },
            )

        # Signal 1: Proportion of follows that are suspect (weight: 0.70)
        suspect_ratio = suspect_count / analyzed_count
        suspect_score = min(100.0, suspect_ratio * 100.0)

        # Signal 2: Absolute count of suspect follows (weight: 0.30)
        # Following 5+ rage bait accounts is very suspicious
        count_score = min(100.0, suspect_count / 5 * 100.0)

        score = suspect_score * 0.70 + count_score * 0.30

        # Confidence increases with more analyzed accounts
        confidence = min(0.9, 0.1 + analyzed_count / len(following) * 0.8)

        return AnalyzerResult(
            score=min(100.0, max(0.0, round(score, 1))),
            confidence=round(confidence, 2),
            details={
                "total_following": len(following),
                "analyzed_in_db": analyzed_count,
                "suspect_count": suspect_count,
                "suspect_handles": suspect_handles[:10],  # Limit for serialization
            },
        )

    async def health_check(self) -> bool:
        return True
