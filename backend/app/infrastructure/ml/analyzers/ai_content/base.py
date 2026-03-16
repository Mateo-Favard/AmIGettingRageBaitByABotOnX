from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.twitter import TweetData


@dataclass(frozen=True)
class StrategyResult:
    """Result from a single AI detection strategy."""

    score: float  # 0.0-1.0 (probability of AI-generated)
    confidence: float  # 0.0-1.0
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            msg = f"score must be 0-1, got {self.score}"
            raise ValueError(msg)
        if not 0 <= self.confidence <= 1:
            msg = f"confidence must be 0-1, got {self.confidence}"
            raise ValueError(msg)


class AIDetectionStrategy(ABC):
    """Internal strategy interface for AI content detection sub-pipeline."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def detect(
        self,
        texts: list[str],
        tweets: list[TweetData],
    ) -> StrategyResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
