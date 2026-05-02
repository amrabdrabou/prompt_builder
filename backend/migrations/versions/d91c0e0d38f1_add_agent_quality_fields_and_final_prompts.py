"""add agent quality fields and final prompts

Revision ID: d91c0e0d38f1
Revises: b7b4e2d8a93c
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd91c0e0d38f1'
down_revision: Union[str, Sequence[str], None] = 'b7b4e2d8a93c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'conversations',
        sa.Column('prompt_type', sa.String(length=50), server_default='other', nullable=False),
    )
    op.add_column(
        'conversations',
        sa.Column('title', sa.String(length=120), server_default='', nullable=False),
    )
    op.add_column(
        'conversations',
        sa.Column(
            'confidence',
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
    )

    op.create_table(
        'final_prompts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('prompt_type', sa.String(length=50), server_default='other', nullable=False),
        sa.Column('quality_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('review', sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_final_prompts_conversation_id'),
        'final_prompts',
        ['conversation_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_final_prompts_conversation_id'), table_name='final_prompts')
    op.drop_table('final_prompts')
    op.drop_column('conversations', 'confidence')
    op.drop_column('conversations', 'title')
    op.drop_column('conversations', 'prompt_type')
