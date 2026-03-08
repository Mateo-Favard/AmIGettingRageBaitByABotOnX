from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.exceptions import TwitterAPIError
from app.domain.interfaces.twitter import TwitterClientInterface
from app.domain.models.twitter import TweetData, TwitterProfile

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.twitterapi.io/twitter"


class TwitterAPIClient(TwitterClientInterface):
    """Real Twitter API client using twitterapi.io."""

    def __init__(
        self,
        api_key: str,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=False,
            headers={
                "X-API-Key": self._api_key,
                "Accept": "application/json",
            },
        )

    async def fetch_profile(self, handle: str) -> TwitterProfile:
        data = await self._request(
            "GET",
            f"{_BASE_URL}/user/info",
            params={"userName": handle},
        )
        user = data.get("data", data)
        return TwitterProfile(
            handle=handle,
            display_name=user.get("name", ""),
            bio=user.get("description", ""),
            profile_image_url=user.get("profilePicture", user.get("profile_image_url_https", "")),
            followers_count=user.get("followers", user.get("followers_count", 0)),
            following_count=user.get("following", user.get("friends_count", 0)),
            tweets_count=user.get("statusesCount", user.get("statuses_count", 0)),
            account_created_at=_parse_datetime(user.get("createdAt", user.get("created_at"))),
        )

    async def fetch_recent_tweets(
        self, handle: str, count: int = 20
    ) -> list[TweetData]:
        data = await self._request(
            "GET",
            f"{_BASE_URL}/user/last_tweets",
            params={"userName": handle, "count": str(count)},
        )
        raw_data = data.get("data", [])
        if isinstance(raw_data, dict):
            tweets_raw = raw_data.get("tweets", [])
        elif isinstance(raw_data, list):
            tweets_raw = raw_data
        else:
            tweets_raw = []
        return [_parse_tweet(t) for t in tweets_raw]

    async def fetch_following(self, handle: str, count: int = 100) -> list[str]:
        data = await self._request(
            "GET",
            f"{_BASE_URL}/user/following",
            params={"userName": handle, "count": str(count)},
        )
        following_raw = data.get("data", [])
        if not isinstance(following_raw, list):
            return []
        return [
            u.get("userName", u.get("screen_name", ""))
            for u in following_raw
            if isinstance(u, dict)
        ]

    async def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._client.request(method, url, **kwargs)
                if response.status_code == 200:
                    return response.json()  # type: ignore[no-any-return]
                if 400 <= response.status_code < 500:
                    raise TwitterAPIError(
                        f"Twitter API returned {response.status_code}: {response.text}",
                        status=response.status_code,
                    )
                # 5xx — retry
                last_exc = TwitterAPIError(
                    f"Twitter API returned {response.status_code}",
                    status=response.status_code,
                )
            except httpx.TimeoutException as exc:
                last_exc = exc
            except TwitterAPIError:
                raise
            except httpx.HTTPError as exc:
                last_exc = exc

            # Exponential backoff: 1s, 2s, 4s
            if attempt < self._max_retries - 1:
                delay = 2**attempt
                logger.warning(
                    "Twitter API attempt %d failed, retrying in %ds",
                    attempt + 1,
                    delay,
                )
                await asyncio.sleep(delay)

        raise TwitterAPIError(
            f"Twitter API failed after {self._max_retries} attempts: {last_exc}",
        )

    async def close(self) -> None:
        await self._client.aclose()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            # Twitter format: "Thu Oct 28 00:00:00 +0000 2021"
            return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            return None


def _parse_tweet(raw: dict[str, Any]) -> TweetData:
    posted_at = _parse_datetime(raw.get("createdAt", raw.get("created_at"))) or datetime.now(tz=UTC)
    return TweetData(
        twitter_id=str(raw.get("id", raw.get("id_str", ""))),
        content=raw.get("text", raw.get("full_text", "")),
        posted_at=posted_at,
        likes_count=raw.get("likeCount", raw.get("favorite_count", 0)),
        retweets_count=raw.get("retweetCount", raw.get("retweet_count", 0)),
        replies_count=raw.get("replyCount", raw.get("reply_count", 0)),
    )
