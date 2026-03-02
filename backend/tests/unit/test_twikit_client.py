"""Tests for TwikitClient with mocked twikit.Client."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import TwitterAPIError
from app.infrastructure.twitter.twikit_client import TwikitClient


def _make_twikit_user(**overrides: object) -> SimpleNamespace:
    defaults = {
        "name": "Test User",
        "description": "A test bio",
        "profile_image_url": "https://pbs.twimg.com/profile/test.jpg",
        "followers_count": 1000,
        "following_count": 200,
        "statuses_count": 5000,
        "created_at": "2020-06-15T00:00:00Z",
        "screen_name": "testuser",
        "get_tweets": AsyncMock(return_value=[]),
        "get_following": AsyncMock(return_value=[]),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_twikit_tweet(**overrides: object) -> SimpleNamespace:
    defaults = {
        "id": "987654321",
        "text": "Hello from twikit!",
        "created_at": "2024-03-01T12:00:00Z",
        "favorite_count": 42,
        "retweet_count": 5,
        "reply_count": 3,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _create_client(cookies_path: str = "/tmp/test_cookies.json") -> TwikitClient:
    return TwikitClient(
        username="user",
        email="user@example.com",
        password="pass123",
        cookies_path=cookies_path,
    )


class TestFetchProfile:
    async def test_maps_fields_correctly(self) -> None:
        client = _create_client()
        client._logged_in = True
        user = _make_twikit_user()

        with patch.object(
            client._client, "get_user_by_screen_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = user
            profile = await client.fetch_profile("testuser")

        assert profile.handle == "testuser"
        assert profile.display_name == "Test User"
        assert profile.bio == "A test bio"
        assert profile.profile_image_url == "https://pbs.twimg.com/profile/test.jpg"
        assert profile.followers_count == 1000
        assert profile.following_count == 200
        assert profile.tweets_count == 5000
        assert profile.account_created_at is not None
        assert profile.account_created_at.year == 2020

    async def test_handles_none_fields(self) -> None:
        client = _create_client()
        client._logged_in = True
        user = _make_twikit_user(
            name=None,
            description=None,
            profile_image_url=None,
            followers_count=None,
            following_count=None,
            statuses_count=None,
            created_at=None,
        )

        with patch.object(
            client._client, "get_user_by_screen_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = user
            profile = await client.fetch_profile("testuser")

        assert profile.display_name == ""
        assert profile.bio == ""
        assert profile.followers_count == 0
        assert profile.account_created_at is None


class TestFetchRecentTweets:
    async def test_maps_fields_correctly(self) -> None:
        client = _create_client()
        client._logged_in = True
        tweet = _make_twikit_tweet()
        user = _make_twikit_user(get_tweets=AsyncMock(return_value=[tweet]))

        with patch.object(
            client._client, "get_user_by_screen_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = user
            tweets = await client.fetch_recent_tweets("testuser", count=10)

        assert len(tweets) == 1
        assert tweets[0].twitter_id == "987654321"
        assert tweets[0].content == "Hello from twikit!"
        assert tweets[0].likes_count == 42
        assert tweets[0].retweets_count == 5
        assert tweets[0].replies_count == 3
        assert tweets[0].posted_at.year == 2024

    async def test_uses_like_count_fallback(self) -> None:
        client = _create_client()
        client._logged_in = True
        tweet = _make_twikit_tweet()
        del tweet.favorite_count
        tweet.like_count = 99
        user = _make_twikit_user(get_tweets=AsyncMock(return_value=[tweet]))

        with patch.object(
            client._client, "get_user_by_screen_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = user
            tweets = await client.fetch_recent_tweets("testuser")

        assert tweets[0].likes_count == 99


class TestFetchFollowing:
    async def test_maps_fields_correctly(self) -> None:
        client = _create_client()
        client._logged_in = True
        following_users = [
            SimpleNamespace(screen_name="alice"),
            SimpleNamespace(screen_name="bob"),
            SimpleNamespace(screen_name="charlie"),
        ]
        user = _make_twikit_user(get_following=AsyncMock(return_value=following_users))

        with patch.object(
            client._client, "get_user_by_screen_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = user
            result = await client.fetch_following("testuser", count=50)

        assert result == ["alice", "bob", "charlie"]

    async def test_skips_none_screen_names(self) -> None:
        client = _create_client()
        client._logged_in = True
        following_users = [
            SimpleNamespace(screen_name="alice"),
            SimpleNamespace(screen_name=None),
            SimpleNamespace(screen_name=""),
        ]
        user = _make_twikit_user(get_following=AsyncMock(return_value=following_users))

        with patch.object(
            client._client, "get_user_by_screen_name", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = user
            result = await client.fetch_following("testuser")

        assert result == ["alice"]


class TestLogin:
    async def test_uses_cookies_if_available(self) -> None:
        client = _create_client()
        mock_load = MagicMock()
        client._client.load_cookies = mock_load

        with patch("pathlib.Path.exists", return_value=True):
            await client._ensure_logged_in()

        mock_load.assert_called_once_with(str(client._cookies_path))
        assert client._logged_in is True

    async def test_login_fallback_to_credentials(self) -> None:
        client = _create_client()
        mock_login = AsyncMock()
        mock_save = MagicMock()
        client._client.login = mock_login
        client._client.save_cookies = mock_save

        with patch("pathlib.Path.exists", return_value=False):
            await client._ensure_logged_in()

        mock_login.assert_called_once_with(
            auth_info_1="user",
            auth_info_2="user@example.com",
            password="pass123",
        )
        mock_save.assert_called_once_with(str(client._cookies_path))
        assert client._logged_in is True

    async def test_skips_if_already_logged_in(self) -> None:
        client = _create_client()
        client._logged_in = True
        mock_load = MagicMock()
        client._client.load_cookies = mock_load

        await client._ensure_logged_in()

        mock_load.assert_not_called()


class TestErrorWrapping:
    async def test_fetch_profile_wraps_exception(self) -> None:
        client = _create_client()
        client._logged_in = True

        with (
            patch.object(
                client._client,
                "get_user_by_screen_name",
                new_callable=AsyncMock,
                side_effect=RuntimeError("connection failed"),
            ),
            pytest.raises(TwitterAPIError, match="fetch_profile failed"),
        ):
            await client.fetch_profile("testuser")

    async def test_fetch_recent_tweets_wraps_exception(self) -> None:
        client = _create_client()
        client._logged_in = True

        with (
            patch.object(
                client._client,
                "get_user_by_screen_name",
                new_callable=AsyncMock,
                side_effect=RuntimeError("timeout"),
            ),
            pytest.raises(TwitterAPIError, match="fetch_recent_tweets failed"),
        ):
            await client.fetch_recent_tweets("testuser")

    async def test_login_wraps_exception(self) -> None:
        client = _create_client()
        mock_login = AsyncMock(side_effect=RuntimeError("bad creds"))
        client._client.login = mock_login

        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(TwitterAPIError, match="login failed"),
        ):
            await client._ensure_logged_in()
