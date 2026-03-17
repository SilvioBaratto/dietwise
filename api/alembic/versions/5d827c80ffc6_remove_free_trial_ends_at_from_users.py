"""remove_free_trial_ends_at_from_users

Revision ID: 5d827c80ffc6
Revises: 06b1d06bfb97
Create Date: 2025-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d827c80ffc6'
down_revision: Union[str, Sequence[str], None] = '06b1d06bfb97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove free_trial_ends_at column and its index."""
    # Drop the index
    op.drop_index('idx_users_trial_status', table_name='users')

    # Drop the column
    op.drop_column('users', 'free_trial_ends_at')


def downgrade() -> None:
    """Restore free_trial_ends_at column and its index."""
    # Restore column
    op.add_column('users', sa.Column(
        'free_trial_ends_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='When the free trial expires (7 days from registration)'
    ))

    # Restore index
    op.create_index('idx_users_trial_status', 'users', ['free_trial_ends_at'], unique=False)
