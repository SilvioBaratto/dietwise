"""add_user_approval_fields

Revision ID: 386492be88b0
Revises: 5d827c80ffc6
Create Date: 2025-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '386492be88b0'
down_revision: Union[str, Sequence[str], None] = '5d827c80ffc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_approved and is_admin fields to users table."""
    # Add is_approved column
    op.add_column('users', sa.Column(
        'is_approved',
        sa.Boolean(),
        server_default='false',
        nullable=False,
        comment='True if user has been approved by admin'
    ))

    # Add is_admin column
    op.add_column('users', sa.Column(
        'is_admin',
        sa.Boolean(),
        server_default='false',
        nullable=False,
        comment='True if user is an admin'
    ))

    # Create index for filtering pending users
    op.create_index('idx_users_approval_status', 'users', ['is_approved'], unique=False)


def downgrade() -> None:
    """Remove is_approved and is_admin fields from users table."""
    op.drop_index('idx_users_approval_status', table_name='users')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'is_approved')
