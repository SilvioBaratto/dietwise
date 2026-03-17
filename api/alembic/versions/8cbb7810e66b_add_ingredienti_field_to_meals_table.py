"""add ingredienti field to meals table

Revision ID: 8cbb7810e66b
Revises: fa70e8b10560
Create Date: 2025-11-06 22:27:41.006487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cbb7810e66b'
down_revision: Union[str, Sequence[str], None] = 'fa70e8b10560'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add ingredienti column to meals table
    op.add_column('meals', sa.Column('ingredienti', sa.String(), nullable=False, server_default=''))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove ingredienti column from meals table
    op.drop_column('meals', 'ingredienti')
