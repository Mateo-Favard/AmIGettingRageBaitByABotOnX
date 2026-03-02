import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin


class TwitterAccount(TimestampMixin, Base):
    __tablename__ = "twitter_accounts"

    handle: Mapped[str] = mapped_column(
        String(15), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(50))
    bio: Mapped[str | None] = mapped_column(Text)
    profile_image_url: Mapped[str | None] = mapped_column(String(500))
    followers_count: Mapped[int] = mapped_column(Integer, default=0)
    following_count: Mapped[int] = mapped_column(Integer, default=0)
    tweets_count: Mapped[int] = mapped_column(Integer, default=0)
    account_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    tweets: Mapped[list["Tweet"]] = relationship(back_populates="account")
    analyses: Mapped[list["AnalysisResult"]] = relationship(back_populates="account")


class Tweet(TimestampMixin, Base):
    __tablename__ = "tweets"

    twitter_id: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    retweets_count: Mapped[int] = mapped_column(Integer, default=0)
    replies_count: Mapped[int] = mapped_column(Integer, default=0)

    account: Mapped["TwitterAccount"] = relationship(back_populates="tweets")


class AnalysisResult(TimestampMixin, Base):
    __tablename__ = "analysis_results"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    ai_content_score: Mapped[float | None] = mapped_column(Float)
    behavioral_score: Mapped[float | None] = mapped_column(Float)
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    political_shift_score: Mapped[float | None] = mapped_column(Float)
    network_score: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_versions: Mapped[dict] = mapped_column(JSONB, default=dict)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    account: Mapped["TwitterAccount"] = relationship(back_populates="analyses")


class SocialRelation(TimestampMixin, Base):
    __tablename__ = "social_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_account_id",
            "target_account_id",
            "relation_type",
            name="uq_social_relation",
        ),
        Index(
            "ix_social_relation_source",
            "source_account_id",
        ),
        Index(
            "ix_social_relation_target",
            "target_account_id",
        ),
    )

    source_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="follows"
    )
