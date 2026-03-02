from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.interfaces.cache import CacheInterface
    from app.domain.interfaces.repositories import (
        AccountRepositoryInterface,
    )
    from app.domain.interfaces.twitter import TwitterClientInterface

from app.domain.models.twitter import AnalysisResultData, TwitterProfile

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        twitter_client: TwitterClientInterface,
        account_repo: AccountRepositoryInterface,
        cache: CacheInterface,
        cache_ttl_seconds: int = 604_800,
    ) -> None:
        self._twitter = twitter_client
        self._repo = account_repo
        self._cache = cache
        self._cache_ttl = cache_ttl_seconds

    async def analyze(
        self, handle: str, *, force: bool = False
    ) -> tuple[AnalysisResultData, bool]:
        """Analyze a Twitter account.

        Returns (result, cached).
        """
        cache_key = f"analysis:{handle}"

        # 1. Check cache (unless force refresh)
        if not force:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                result = _deserialize_analysis(cached)
                logger.info("Cache hit for %s", handle)
                return result, True

        # 2. Fetch Twitter data
        profile = await self._twitter.fetch_profile(handle)
        tweets = await self._twitter.fetch_recent_tweets(handle)

        # 3. Upsert account
        account_id = await self._repo.upsert(profile)

        # 4. Save tweets
        await self._repo.save_tweets(account_id, tweets)

        # 5. Compute score (placeholder heuristic)
        score = _compute_placeholder_score(profile)

        # 6. Build result
        now = datetime.now(tz=UTC)
        result = AnalysisResultData(
            account_id=account_id,
            handle=handle,
            composite_score=score,
            analyzed_at=now,
            behavioral_score=score,
            details={
                "method": "placeholder_heuristic",
                "version": "0.1.0",
            },
            model_versions={"scoring": "placeholder_v1"},
        )

        # 7. Persist analysis
        await self._repo.save_analysis(result)

        # 8. Cache result
        await self._cache.set(cache_key, _serialize_analysis(result), self._cache_ttl)

        logger.info("Analysis complete for %s: score=%.1f", handle, score)
        return result, False


def _compute_placeholder_score(profile: TwitterProfile) -> float:
    """Simple heuristic: high followers/following ratio.

    Capped at 50. Replaced by ML pipeline in Phase 3.
    """
    if profile.following_count == 0:
        ratio = float(profile.followers_count)
    else:
        ratio = profile.followers_count / profile.following_count

    # Normalize: ratio > 1000 -> max, ratio < 2 -> near 0
    if ratio <= 2:
        score = 0.0
    elif ratio >= 1000:
        score = 50.0
    else:
        score = min(50.0, (ratio - 2) / (1000 - 2) * 50.0)

    return round(score, 1)


def _serialize_analysis(result: AnalysisResultData) -> str:
    data: dict[str, Any] = {
        "account_id": str(result.account_id),
        "handle": result.handle,
        "composite_score": result.composite_score,
        "analyzed_at": result.analyzed_at.isoformat(),
        "ai_content_score": result.ai_content_score,
        "behavioral_score": result.behavioral_score,
        "sentiment_score": result.sentiment_score,
        "political_shift_score": result.political_shift_score,
        "network_score": result.network_score,
        "details": result.details,
        "model_versions": result.model_versions,
    }
    return json.dumps(data)


def _deserialize_analysis(raw: str) -> AnalysisResultData:
    data = json.loads(raw)
    return AnalysisResultData(
        account_id=uuid.UUID(data["account_id"]),
        handle=data["handle"],
        composite_score=data["composite_score"],
        analyzed_at=datetime.fromisoformat(data["analyzed_at"]),
        ai_content_score=data.get("ai_content_score"),
        behavioral_score=data.get("behavioral_score"),
        sentiment_score=data.get("sentiment_score"),
        political_shift_score=data.get("political_shift_score"),
        network_score=data.get("network_score"),
        details=data.get("details", {}),
        model_versions=data.get("model_versions", {}),
    )
