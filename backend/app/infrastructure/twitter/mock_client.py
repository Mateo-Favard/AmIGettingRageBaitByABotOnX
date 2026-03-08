from datetime import UTC, datetime, timedelta

from app.domain.interfaces.twitter import TwitterClientInterface
from app.domain.models.twitter import TweetData, TwitterProfile

_NORMAL_PROFILES: dict[str, TwitterProfile] = {
    "journo_marie": TwitterProfile(
        handle="journo_marie",
        display_name="Marie Dupont",
        bio="Journaliste indépendante. Politique, société, culture.",
        followers_count=12_500,
        following_count=890,
        tweets_count=8_400,
        account_created_at=datetime(2015, 3, 12, tzinfo=UTC),
    ),
    "devweb_alex": TwitterProfile(
        handle="devweb_alex",
        display_name="Alex Martin",
        bio="Développeur full-stack. TypeScript, Python. Open source.",
        followers_count=3_200,
        following_count=1_100,
        tweets_count=4_500,
        account_created_at=datetime(2017, 8, 5, tzinfo=UTC),
    ),
}

_SUSPECT_PROFILES: dict[str, TwitterProfile] = {
    "suspect_bot42": TwitterProfile(
        handle="suspect_bot42",
        display_name="Patriote2024 🇫🇷",
        bio="LA VÉRITÉ QU'ON VOUS CACHE !!! Réveillez-vous !",
        followers_count=45_000,
        following_count=12,
        tweets_count=98_000,
        account_created_at=datetime(2023, 11, 1, tzinfo=UTC),
    ),
    "suspect_rage": TwitterProfile(
        handle="suspect_rage",
        display_name="InfoChoc",
        bio="SCANDALEUX ce que fait le gouvernement",
        followers_count=22_000,
        following_count=8,
        tweets_count=150_000,
        account_created_at=datetime(2024, 1, 15, tzinfo=UTC),
    ),
}

_ALL_PROFILES: dict[str, TwitterProfile] = {**_NORMAL_PROFILES, **_SUSPECT_PROFILES}

_NOW = datetime.now(tz=UTC)


def _generate_normal_tweets(handle: str, count: int) -> list[TweetData]:
    templates = [
        "Intéressant cet article sur la réforme des retraites.",
        "Belle journée pour coder en Python 🐍",
        "Quelqu'un a testé le nouveau framework ? Des retours ?",
        "Thread sur les dernières évolutions du marché tech ⬇️",
        "Bon week-end à tous !",
    ]
    tweets = []
    for i in range(min(count, len(templates))):
        tweets.append(
            TweetData(
                twitter_id=f"normal_{handle}_{i}",
                content=templates[i],
                posted_at=_NOW - timedelta(hours=i * 6),
                likes_count=15 + i * 3,
                retweets_count=2 + i,
                replies_count=5 + i,
            )
        )
    return tweets


def _generate_suspect_tweets(handle: str, count: int) -> list[TweetData]:
    templates = [
        "🚨 URGENT 🚨 ILS VEULENT NOUS CACHER LA VÉRITÉ !!! PARTAGEZ !!!",
        "SCANDALEUX !!! Le gouvernement nous MENT depuis le début !!!",
        "RT si vous en avez MARRE de cette DICTATURE !!!",
        "Les MÉDIAS sont COMPLICES !!! Ouvrez les YEUX !!!",
        "🔴 ALERTE 🔴 Ce que les élites ne veulent pas que vous sachiez...",
    ]
    tweets = []
    for i in range(min(count, len(templates))):
        tweets.append(
            TweetData(
                twitter_id=f"suspect_{handle}_{i}",
                content=templates[i],
                posted_at=_NOW - timedelta(minutes=i * 15),
                likes_count=800 + i * 200,
                retweets_count=500 + i * 100,
                replies_count=300 + i * 50,
            )
        )
    return tweets


class MockTwitterClient(TwitterClientInterface):
    """Mock Twitter client using fake data.

    Used at runtime when TWITTER_API_KEY is empty.
    Handles starting with 'suspect_' return suspicious-looking data.
    """

    async def fetch_profile(self, handle: str) -> TwitterProfile:
        if handle in _ALL_PROFILES:
            return _ALL_PROFILES[handle]

        # Default: generate a generic profile
        is_suspect = handle.startswith("suspect_")
        if is_suspect:
            return TwitterProfile(
                handle=handle,
                display_name=f"SuspectUser_{handle}",
                bio="RÉVEILLEZ-VOUS !!! PARTAGEZ !!!",
                followers_count=30_000,
                following_count=5,
                tweets_count=120_000,
                account_created_at=datetime(2024, 6, 1, tzinfo=UTC),
            )
        return TwitterProfile(
            handle=handle,
            display_name=f"User {handle}",
            bio=f"Just a regular user @{handle}",
            followers_count=500,
            following_count=400,
            tweets_count=1_200,
            account_created_at=datetime(2018, 1, 1, tzinfo=UTC),
        )

    async def fetch_recent_tweets(
        self, handle: str, count: int = 20
    ) -> list[TweetData]:
        is_suspect = handle.startswith("suspect_")
        if is_suspect:
            return _generate_suspect_tweets(handle, count)
        return _generate_normal_tweets(handle, count)

    async def fetch_following(self, handle: str, count: int = 100) -> list[str]:
        is_suspect = handle.startswith("suspect_")
        if is_suspect:
            return ["suspect_bot42", "suspect_rage", "infochoc_media"]
        return ["journo_marie", "devweb_alex", "lemonde", "bbc_world"]

    async def search_tweets(
        self, query: str, query_type: str = "Latest"
    ) -> list[TweetData]:
        # Return suspect or normal tweets based on query content
        if "suspect_" in query:
            return _generate_suspect_tweets("mock_search", 5)
        return _generate_normal_tweets("mock_search", 5)

    async def fetch_trends(self, woeid: int = 615702) -> list[str]:
        return [
            "Réforme des retraites",
            "Immigration",
            "Macron",
            "Ligue 1",
            "ChatGPT",
        ]
