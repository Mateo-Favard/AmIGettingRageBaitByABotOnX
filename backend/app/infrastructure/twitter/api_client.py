from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
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
        self, handle: str, count: int = 20, weeks: int = 5
    ) -> list[TweetData]:
        """Fetch tweets spread across the last N weeks using Advanced Search.

        Makes one search per week (from:{handle} since:... until:...),
        filtering out retweets. Costs 1 API call per week.
        """
        now = datetime.now(tz=UTC)
        all_tweets: list[TweetData] = []

        for week_idx in range(weeks):
            week_end = now - timedelta(weeks=week_idx)
            week_start = now - timedelta(weeks=week_idx + 1)
            since = week_start.strftime("%Y-%m-%d")
            until = week_end.strftime("%Y-%m-%d")

            query = f"from:{handle} -filter:retweets since:{since} until:{until}"
            tweets = await self.search_tweets(query)
            all_tweets.extend(tweets)

        return all_tweets

    async def search_tweets(
        self, query: str, query_type: str = "Latest"
    ) -> list[TweetData]:
        data = await self._request(
            "GET",
            f"{_BASE_URL}/tweet/advanced_search",
            params={"query": query, "queryType": query_type},
        )
        tweets_raw = data.get("tweets", [])
        return [
            _parse_tweet(t) for t in tweets_raw
            if isinstance(t, dict) and not t.get("text", "").startswith("RT @")
        ]

    async def fetch_trends(self, woeid: int = 615702) -> list[str]:
        """Fetch current trending topics. Default woeid=615702 (France)."""
        data = await self._request(
            "GET",
            f"{_BASE_URL}/trends",
            params={"woeid": str(woeid)},
        )
        trends_raw = data.get("trends", [])
        return [t.get("name", "") for t in trends_raw if isinstance(t, dict)]

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
