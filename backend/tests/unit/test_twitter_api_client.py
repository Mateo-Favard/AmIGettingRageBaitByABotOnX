"""Tests for TwitterAPIClient without hitting the real API."""

import httpx
import pytest

from app.core.exceptions import TwitterAPIError
from app.infrastructure.twitter.api_client import (
    TwitterAPIClient,
    _parse_datetime,
    _parse_tweet,
)


class TestParseDateTime:
    def test_iso_format(self) -> None:
        result = _parse_datetime("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1

    def test_twitter_format(self) -> None:
        result = _parse_datetime("Thu Oct 28 00:00:00 +0000 2021")
        assert result is not None
        assert result.year == 2021

    def test_none_input(self) -> None:
        assert _parse_datetime(None) is None

    def test_invalid_format(self) -> None:
        assert _parse_datetime("not-a-date") is None


class TestParseTweet:
    def test_parse_full_tweet(self) -> None:
        raw = {
            "id_str": "123456789",
            "full_text": "Hello world!",
            "created_at": "2024-01-15T10:30:00Z",
            "favorite_count": 42,
            "retweet_count": 5,
            "reply_count": 3,
        }
        tweet = _parse_tweet(raw)
        assert tweet.twitter_id == "123456789"
        assert tweet.content == "Hello world!"
        assert tweet.likes_count == 42

    def test_parse_minimal_tweet(self) -> None:
        raw = {"text": "Hi", "id": 999}
        tweet = _parse_tweet(raw)
        assert tweet.content == "Hi"
        assert tweet.twitter_id == "999"
        assert tweet.likes_count == 0


class TestTwitterAPIClientInit:
    def test_client_settings(self) -> None:
        client = TwitterAPIClient(api_key="test-key", timeout=5, max_retries=2)
        assert client._api_key == "test-key"
        assert client._timeout == 5
        assert client._max_retries == 2

    def test_no_follow_redirects(self) -> None:
        client = TwitterAPIClient(api_key="test-key")
        assert client._client.follow_redirects is False


class TestTwitterAPIClientRequest:
    async def test_4xx_raises_without_retry(self) -> None:
        client = TwitterAPIClient(api_key="test-key", max_retries=1)

        async def mock_request(*args: object, **kwargs: object) -> httpx.Response:
            return httpx.Response(
                status_code=404,
                text="Not found",
                request=httpx.Request("GET", "https://test.com"),
            )

        client._client.request = mock_request  # type: ignore[assignment]

        with pytest.raises(TwitterAPIError, match="404"):
            await client._request("GET", "https://test.com/endpoint")
