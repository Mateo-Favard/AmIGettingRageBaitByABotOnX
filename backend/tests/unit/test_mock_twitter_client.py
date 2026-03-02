import pytest

from app.infrastructure.twitter.mock_client import MockTwitterClient


@pytest.fixture
def mock_client() -> MockTwitterClient:
    return MockTwitterClient()


class TestMockTwitterClientProfile:
    async def test_fetch_known_normal_profile(
        self, mock_client: MockTwitterClient
    ) -> None:
        profile = await mock_client.fetch_profile("journo_marie")
        assert profile.handle == "journo_marie"
        assert profile.followers_count == 12_500

    async def test_fetch_known_suspect_profile(
        self, mock_client: MockTwitterClient
    ) -> None:
        profile = await mock_client.fetch_profile("suspect_bot42")
        assert profile.handle == "suspect_bot42"
        assert profile.followers_count == 45_000
        assert profile.following_count == 12

    async def test_fetch_unknown_normal_handle(
        self, mock_client: MockTwitterClient
    ) -> None:
        profile = await mock_client.fetch_profile("random_user")
        assert profile.handle == "random_user"
        assert profile.followers_count == 500

    async def test_fetch_unknown_suspect_handle(
        self, mock_client: MockTwitterClient
    ) -> None:
        profile = await mock_client.fetch_profile("suspect_newbot")
        assert profile.handle == "suspect_newbot"
        assert profile.followers_count == 30_000
        assert profile.following_count == 5


class TestMockTwitterClientTweets:
    async def test_normal_tweets(self, mock_client: MockTwitterClient) -> None:
        tweets = await mock_client.fetch_recent_tweets("devweb_alex", count=3)
        assert len(tweets) == 3
        assert all("!!!" not in t.content for t in tweets)

    async def test_suspect_tweets(self, mock_client: MockTwitterClient) -> None:
        tweets = await mock_client.fetch_recent_tweets("suspect_bot42", count=3)
        assert len(tweets) == 3
        assert all("!!!" in t.content for t in tweets)

    async def test_tweet_count_capped(self, mock_client: MockTwitterClient) -> None:
        tweets = await mock_client.fetch_recent_tweets("devweb_alex", count=100)
        assert len(tweets) <= 5  # capped by template count


class TestMockTwitterClientFollowing:
    async def test_normal_following(self, mock_client: MockTwitterClient) -> None:
        following = await mock_client.fetch_following("devweb_alex")
        assert "lemonde" in following

    async def test_suspect_following(self, mock_client: MockTwitterClient) -> None:
        following = await mock_client.fetch_following("suspect_bot42")
        assert "suspect_rage" in following
