from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.models.twitter import TweetData, TwitterProfile


class TwitterClientInterface(ABC):
    @abstractmethod
    async def fetch_profile(self, handle: str) -> TwitterProfile: ...

    @abstractmethod
    async def fetch_recent_tweets(
        self, handle: str, count: int = 20
    ) -> list[TweetData]: ...

    @abstractmethod
    async def fetch_following(self, handle: str, count: int = 100) -> list[str]: ...
