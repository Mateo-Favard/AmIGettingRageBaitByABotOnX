"""Client Twitter gratuit utilisant twikit (login-based).

Twikit utilise l'API interne de Twitter (celle du site web) via un login
username/email/password. Pas besoin de cle API payante, mais sujet aux
rate limits de Twitter et aux risques de lock de compte.

Priorite de selection (dans dependencies.py) :
  1. TwitterAPIClient  — API payante twitterapi.io
  2. TwikitClient      — Ce client (gratuit, credentials Twitter)
  3. MockTwitterClient  — Donnees fake (fallback dev/test)

Limitations :
  - 1 session = 1 compte Twitter (pas de pool)
  - ~50-100 req/15min avant rate limit Twitter
  - Lock possible si surutilisation
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from twikit import Client

from app.core.exceptions import TwitterAPIError
from app.domain.interfaces.twitter import TwitterClientInterface
from app.domain.models.twitter import TweetData, TwitterProfile

logger = logging.getLogger(__name__)

# Path par defaut pour la persistance des cookies de session Twitter.
# Utilise /tmp car le container Docker est ephemere ; en prod,
# monter un volume persistant pour eviter les re-logins.
_DEFAULT_COOKIES_PATH = "/tmp/twikit_cookies.json"  # noqa: S108


class TwikitClient(TwitterClientInterface):
    """Client Twitter gratuit via twikit (API interne Twitter).

    Gere automatiquement le login et la persistance de session
    via cookies. Chaque appel public verifie que la session est
    active avant d'executer la requete.
    """

    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        cookies_path: str = _DEFAULT_COOKIES_PATH,
    ) -> None:
        self._username = username
        self._email = email
        self._password = password
        self._cookies_path = Path(cookies_path)
        # "fr-FR" pour que Twitter retourne le contenu localise en francais
        self._client = Client("fr-FR")
        self._logged_in = False

    async def _ensure_logged_in(self) -> None:
        """Garantit que le client est authentifie aupres de Twitter.

        Strategie en 2 etapes :
          1. Charger les cookies depuis le fichier (rapide, pas de requete)
          2. Si pas de cookies : login complet + sauvegarde cookies

        Le flag _logged_in evite de re-verifier a chaque appel une fois
        la session etablie dans le meme cycle de vie du client.
        """
        if self._logged_in:
            return
        try:
            if self._cookies_path.exists():
                self._client.load_cookies(str(self._cookies_path))
                self._logged_in = True
                logger.info("Twikit: loaded cookies from %s", self._cookies_path)
                return
        except Exception:
            logger.warning("Twikit: failed to load cookies, falling back to login")

        try:
            await self._client.login(
                auth_info_1=self._username,
                auth_info_2=self._email,
                password=self._password,
            )
            self._client.save_cookies(str(self._cookies_path))
            self._logged_in = True
            logger.info("Twikit: logged in and saved cookies")
        except Exception as exc:
            raise TwitterAPIError(
                f"Twikit login failed: {exc}",
            ) from exc

    async def fetch_profile(self, handle: str) -> TwitterProfile:
        """Recupere le profil Twitter d'un utilisateur par son handle.

        Mappe les champs twikit vers le modele domain TwitterProfile.
        Les champs None sont remplaces par des valeurs par defaut
        (chaine vide ou 0) pour garantir la coherence du domain.
        """
        await self._ensure_logged_in()
        try:
            user = await self._client.get_user_by_screen_name(handle)
        except Exception as exc:
            raise TwitterAPIError(
                f"Twikit fetch_profile failed for @{handle}: {exc}",
            ) from exc

        return TwitterProfile(
            handle=handle,
            display_name=user.name or "",
            bio=user.description or "",
            profile_image_url=user.profile_image_url or "",
            followers_count=user.followers_count or 0,
            following_count=user.following_count or 0,
            tweets_count=user.statuses_count or 0,
            account_created_at=_parse_created_at(user.created_at),
        )

    async def fetch_recent_tweets(
        self, handle: str, count: int = 20
    ) -> list[TweetData]:
        """Recupere les derniers tweets d'un utilisateur.

        Necessite 2 appels API : d'abord get_user pour obtenir l'objet
        User, puis user.get_tweets pour les tweets. Chaque tweet est
        mappe vers le modele domain TweetData.
        """
        await self._ensure_logged_in()
        try:
            user = await self._client.get_user_by_screen_name(handle)
            tweets = await user.get_tweets("Tweets", count)
        except Exception as exc:
            raise TwitterAPIError(
                f"Twikit fetch_recent_tweets failed for @{handle}: {exc}",
            ) from exc

        return [_map_tweet(t) for t in tweets]

    async def fetch_following(self, handle: str, count: int = 100) -> list[str]:
        """Recupere la liste des comptes suivis par un utilisateur.

        Retourne uniquement les screen_names (handles) des comptes
        suivis. Les entrees sans screen_name sont filtrees.
        """
        await self._ensure_logged_in()
        try:
            user = await self._client.get_user_by_screen_name(handle)
            following = await user.get_following(count)
        except Exception as exc:
            raise TwitterAPIError(
                f"Twikit fetch_following failed for @{handle}: {exc}",
            ) from exc

        return [u.screen_name for u in following if u.screen_name]

    async def search_tweets(
        self, query: str, query_type: str = "Latest"
    ) -> list[TweetData]:
        await self._ensure_logged_in()
        try:
            results = await self._client.search_tweet(query, product=query_type)
        except Exception as exc:
            raise TwitterAPIError(
                f"Twikit search_tweets failed: {exc}",
            ) from exc
        return [_map_tweet(t) for t in results]

    async def fetch_trends(self, woeid: int = 615702) -> list[str]:
        # Twikit doesn't support trends natively
        return []


def _parse_created_at(value: str | None) -> datetime | None:
    """Parse une date de creation de compte Twitter.

    Supporte 2 formats :
      - ISO 8601 : "2020-06-15T00:00:00Z"
      - Format historique Twitter : "Thu Oct 28 00:00:00 +0000 2021"

    Retourne None si le parsing echoue (robustesse face aux
    changements de format de l'API interne).
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return None


def _map_tweet(tweet: object) -> TweetData:
    """Mappe un objet tweet twikit vers le modele domain TweetData.

    Le type est `object` car twikit n'expose pas de type public stable.
    On utilise getattr pour acceder aux champs de maniere defensive.

    Le champ likes a 2 noms possibles dans l'API Twitter interne :
    favorite_count (ancien) et like_count (nouveau).
    """
    posted_at = _parse_created_at(getattr(tweet, "created_at", None))
    if posted_at is None:
        posted_at = datetime.now(tz=UTC)

    # L'API Twitter utilise "favorite_count" ou "like_count" selon la version
    likes = getattr(tweet, "favorite_count", None)
    if likes is None:
        likes = getattr(tweet, "like_count", 0)

    return TweetData(
        twitter_id=str(getattr(tweet, "id", "")),
        content=getattr(tweet, "text", ""),
        posted_at=posted_at,
        likes_count=likes or 0,
        retweets_count=getattr(tweet, "retweet_count", 0) or 0,
        replies_count=getattr(tweet, "reply_count", 0) or 0,
    )
