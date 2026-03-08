from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.repositories import AccountRepositoryInterface
from app.domain.models.twitter import (
    AnalysisResultData,
    TweetData,
    TwitterProfile,
)
from app.infrastructure.db.models import (
    AnalysisResult,
    Tweet,
    TwitterAccount,
)


class AccountRepository(AccountRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_handle(
        self, handle: str
    ) -> tuple[uuid.UUID, TwitterProfile] | None:
        stmt = select(TwitterAccount).where(TwitterAccount.handle == handle)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return row.id, _to_domain_profile(row)

    async def upsert(self, profile: TwitterProfile) -> uuid.UUID:
        stmt = pg_insert(TwitterAccount).values(
            handle=profile.handle,
            display_name=profile.display_name,
            bio=profile.bio,
            profile_image_url=profile.profile_image_url,
            followers_count=profile.followers_count,
            following_count=profile.following_count,
            tweets_count=profile.tweets_count,
            account_created_at=profile.account_created_at,
            last_fetched_at=datetime.now(tz=UTC),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["handle"],
            set_={
                "display_name": stmt.excluded.display_name,
                "bio": stmt.excluded.bio,
                "profile_image_url": stmt.excluded.profile_image_url,
                "followers_count": stmt.excluded.followers_count,
                "following_count": stmt.excluded.following_count,
                "tweets_count": stmt.excluded.tweets_count,
                "account_created_at": stmt.excluded.account_created_at,
                "last_fetched_at": stmt.excluded.last_fetched_at,
            },
        ).returning(TwitterAccount.id)

        result = await self._session.execute(stmt)
        account_id = result.scalar_one()
        await self._session.flush()
        return account_id  # type: ignore[return-value]

    async def save_tweets(self, account_id: uuid.UUID, tweets: list[TweetData]) -> None:
        for tweet in tweets:
            stmt = pg_insert(Tweet).values(
                twitter_id=tweet.twitter_id,
                account_id=account_id,
                content=tweet.content,
                posted_at=tweet.posted_at,
                likes_count=tweet.likes_count,
                retweets_count=tweet.retweets_count,
                replies_count=tweet.replies_count,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["twitter_id"],
                set_={
                    "content": stmt.excluded.content,
                    "likes_count": stmt.excluded.likes_count,
                    "retweets_count": stmt.excluded.retweets_count,
                    "replies_count": stmt.excluded.replies_count,
                },
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def save_analysis(self, result: AnalysisResultData) -> None:
        analysis = AnalysisResult(
            account_id=result.account_id,
            composite_score=result.composite_score,
            ai_content_score=result.ai_content_score,
            behavioral_score=result.behavioral_score,
            sentiment_score=result.sentiment_score,
            opportunism_score=result.opportunism_score,
            details=result.details,
            model_versions=result.model_versions,
            analyzed_at=result.analyzed_at,
        )
        self._session.add(analysis)
        await self._session.flush()

    async def get_latest_analysis(self, handle: str) -> AnalysisResultData | None:
        stmt = (
            select(AnalysisResult)
            .join(TwitterAccount)
            .where(TwitterAccount.handle == handle)
            .order_by(AnalysisResult.analyzed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_domain_analysis(row, handle)

    async def delete_by_handle(self, handle: str) -> bool:
        stmt = select(TwitterAccount.id).where(TwitterAccount.handle == handle)
        result = await self._session.execute(stmt)
        account_id = result.scalar_one_or_none()
        if account_id is None:
            return False

        await self._session.execute(
            delete(TwitterAccount).where(TwitterAccount.id == account_id)
        )
        await self._session.commit()
        return True


def _to_domain_profile(row: TwitterAccount) -> TwitterProfile:
    return TwitterProfile(
        handle=row.handle,
        display_name=row.display_name or "",
        bio=row.bio or "",
        profile_image_url=row.profile_image_url or "",
        followers_count=row.followers_count,
        following_count=row.following_count,
        tweets_count=row.tweets_count,
        account_created_at=row.account_created_at,
    )


def _to_domain_analysis(row: AnalysisResult, handle: str) -> AnalysisResultData:
    return AnalysisResultData(
        account_id=row.account_id,
        handle=handle,
        composite_score=row.composite_score,
        analyzed_at=row.analyzed_at,
        ai_content_score=row.ai_content_score,
        behavioral_score=row.behavioral_score,
        sentiment_score=row.sentiment_score,
        opportunism_score=row.opportunism_score,
        details=row.details,
        model_versions=row.model_versions,
    )
