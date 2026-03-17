"""remove_has_paid_from_users

Revision ID: 06b1d06bfb97
Revises: c26db5a9ab70
Create Date: 2025-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06b1d06bfb97'
down_revision: Union[str, Sequence[str], None] = 'c26db5a9ab70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove has_paid column and update index."""
    # Drop the old index that included has_paid
    op.drop_index('idx_users_trial_status', table_name='users')

    # Drop the has_paid column
    op.drop_column('users', 'has_paid')

    # Create new index without has_paid
    op.create_index('idx_users_trial_status', 'users', ['free_trial_ends_at'], unique=False)


def downgrade() -> None:
    """Restore has_paid column and original index."""
    # Drop the new index
    op.drop_index('idx_users_trial_status', table_name='users')

    # Restore has_paid column
    op.add_column('users', sa.Column(
        'has_paid',
        sa.Boolean(),
        server_default='false',
        nullable=False,
        comment='True if user has paid for current month'
    ))

    # Restore original index with has_paid
    op.create_index('idx_users_trial_status', 'users', ['free_trial_ends_at', 'has_paid'], unique=False)
