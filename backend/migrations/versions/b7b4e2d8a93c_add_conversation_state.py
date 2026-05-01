"""add conversation state

Revision ID: b7b4e2d8a93c
Revises: caadf5750f12
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7b4e2d8a93c'
down_revision: Union[str, Sequence[str], None] = 'caadf5750f12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'conversations',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
    )
    op.add_column(
        'conversations',
        sa.Column('goal', sa.Text(), server_default='', nullable=False),
    )
    op.add_column(
        'conversations',
        sa.Column('audience', sa.Text(), server_default='', nullable=False),
    )
    op.add_column(
        'conversations',
        sa.Column(
            'constraints',
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        'conversations',
        sa.Column('output_format', sa.Text(), server_default='', nullable=False),
    )
    op.add_column(
        'conversations',
        sa.Column(
            'missing_fields',
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        'conversations',
        sa.Column(
            'ready_to_finalize',
            sa.Boolean(),
            server_default=sa.text('false'),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('conversations', 'ready_to_finalize')
    op.drop_column('conversations', 'missing_fields')
    op.drop_column('conversations', 'output_format')
    op.drop_column('conversations', 'constraints')
    op.drop_column('conversations', 'audience')
    op.drop_column('conversations', 'goal')
    op.drop_column('conversations', 'updated_at')
