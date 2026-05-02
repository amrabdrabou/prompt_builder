"""add rate limit events

Revision ID: a21c7f4d9e30
Revises: e6d8f4c2b9a1
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a21c7f4d9e30"
down_revision: Union[str, None] = "e6d8f4c2b9a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action IN ('chat')",
            name="ck_rate_limit_events_action",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rate_limit_events_user_id"),
        "rate_limit_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_rate_limit_events_user_action_created_at",
        "rate_limit_events",
        ["user_id", "action", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_rate_limit_events_user_action_created_at",
        table_name="rate_limit_events",
    )
    op.drop_index(
        op.f("ix_rate_limit_events_user_id"),
        table_name="rate_limit_events",
    )
    op.drop_table("rate_limit_events")
