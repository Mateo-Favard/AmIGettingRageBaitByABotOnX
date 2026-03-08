from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.twitter import TweetData, TwitterProfile


@dataclass(frozen=True)
class AnalysisInput:
    """Immutable bundle of data sent to every analyzer."""

    profile: TwitterProfile
    tweets: list[TweetData]
    following: list[str]


@dataclass(frozen=True)
class AnalyzerResult:
    """Result returned by a single analyzer."""

    score: float  # 0-100
    confidence: float  # 0.0-1.0
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            msg = f"score must be 0-100, got {self.score}"
            raise ValueError(msg)
        if not 0 <= self.confidence <= 1:
            msg = f"confidence must be 0-1, got {self.confidence}"
            raise ValueError(msg)


class AnalyzerInterface(ABC):
    """Common interface for all rage-bait signal analyzers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    async def analyze(self, data: AnalysisInput) -> AnalyzerResult: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
