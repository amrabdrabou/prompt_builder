"""add validation check constraints

Revision ID: e6d8f4c2b9a1
Revises: d91c0e0d38f1
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e6d8f4c2b9a1"
down_revision: Union[str, None] = "d91c0e0d38f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROMPT_TYPES = (
    "writing",
    "coding",
    "marketing",
    "analysis",
    "research",
    "planning",
    "image_generation",
    "automation",
    "other",
)

PROMPT_TYPE_CHECK_SQL = (
    "prompt_type IN ("
    + ", ".join(f"'{prompt_type}'" for prompt_type in PROMPT_TYPES)
    + ")"
)


def upgrade() -> None:
    op.create_check_constraint(
        "ck_conversations_prompt_type",
        "conversations",
        PROMPT_TYPE_CHECK_SQL,
    )
    op.create_check_constraint(
        "ck_final_prompts_prompt_type",
        "final_prompts",
        PROMPT_TYPE_CHECK_SQL,
    )
    op.create_check_constraint(
        "ck_final_prompts_quality_score_range",
        "final_prompts",
        "quality_score >= 0 AND quality_score <= 100",
    )
    op.create_check_constraint(
        "ck_messages_role",
        "messages",
        "role IN ('user', 'assistant')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_messages_role",
        "messages",
        type_="check",
    )
    op.drop_constraint(
        "ck_final_prompts_quality_score_range",
        "final_prompts",
        type_="check",
    )
    op.drop_constraint(
        "ck_final_prompts_prompt_type",
        "final_prompts",
        type_="check",
    )
    op.drop_constraint(
        "ck_conversations_prompt_type",
        "conversations",
        type_="check",
    )
