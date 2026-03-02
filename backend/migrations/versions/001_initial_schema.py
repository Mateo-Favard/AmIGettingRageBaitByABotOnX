"""Initial schema: twitter_accounts, tweets, analysis_results, social_relations

Revision ID: 001_initial
Revises:
Create Date: 2026-03-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "twitter_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("handle", sa.String(15), unique=True, index=True, nullable=False),
        sa.Column("display_name", sa.String(50), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("profile_image_url", sa.String(500), nullable=True),
        sa.Column("followers_count", sa.Integer, default=0),
        sa.Column("following_count", sa.Integer, default=0),
        sa.Column("tweets_count", sa.Integer, default=0),
        sa.Column("account_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "tweets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("twitter_id", sa.String(30), unique=True, index=True, nullable=False),
        sa.Column(
            "account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("likes_count", sa.Integer, default=0),
        sa.Column("retweets_count", sa.Integer, default=0),
        sa.Column("replies_count", sa.Integer, default=0),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("composite_score", sa.Float, nullable=False),
        sa.Column("ai_content_score", sa.Float, nullable=True),
        sa.Column("behavioral_score", sa.Float, nullable=True),
        sa.Column("sentiment_score", sa.Float, nullable=True),
        sa.Column("political_shift_score", sa.Float, nullable=True),
        sa.Column("network_score", sa.Float, nullable=True),
        sa.Column("details", JSONB, default={}),
        sa.Column("model_versions", JSONB, default={}),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "social_relations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("twitter_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(20), nullable=False, default="follows"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "source_account_id",
            "target_account_id",
            "relation_type",
            name="uq_social_relation",
        ),
    )

    op.create_index(
        "ix_social_relation_source",
        "social_relations",
        ["source_account_id"],
    )
    op.create_index(
        "ix_social_relation_target",
        "social_relations",
        ["target_account_id"],
    )


def downgrade() -> None:
    op.drop_table("social_relations")
    op.drop_table("analysis_results")
    op.drop_table("tweets")
    op.drop_table("twitter_accounts")
