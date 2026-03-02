from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from app.domain.models.twitter import (
        AnalysisResultData,
        TweetData,
        TwitterProfile,
    )


class AccountRepositoryInterface(ABC):
    @abstractmethod
    async def get_by_handle(
        self, handle: str
    ) -> tuple[uuid.UUID, TwitterProfile] | None: ...

    @abstractmethod
    async def upsert(self, profile: TwitterProfile) -> uuid.UUID: ...

    @abstractmethod
    async def save_tweets(
        self, account_id: uuid.UUID, tweets: list[TweetData]
    ) -> None: ...

    @abstractmethod
    async def save_analysis(self, result: AnalysisResultData) -> None: ...

    @abstractmethod
    async def get_latest_analysis(self, handle: str) -> AnalysisResultData | None: ...
