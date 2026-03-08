"""Rename political_shift_score/network_score to opportunism_score

Revision ID: 002_opportunism
Revises: 001_initial
Create Date: 2026-03-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_opportunism"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_results",
        sa.Column("opportunism_score", sa.Float(), nullable=True),
    )
    op.drop_column("analysis_results", "political_shift_score")
    op.drop_column("analysis_results", "network_score")


def downgrade() -> None:
    op.add_column(
        "analysis_results",
        sa.Column("political_shift_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "analysis_results",
        sa.Column("network_score", sa.Float(), nullable=True),
    )
    op.drop_column("analysis_results", "opportunism_score")
