"""add_user_api_keys_and_preferences

Revision ID: 29bd1b08a18d
Revises: a4bb3ba2cc9b
Create Date: 2026-03-17 15:18:29.214059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29bd1b08a18d'
down_revision: Union[str, Sequence[str], None] = 'a4bb3ba2cc9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_api_keys table
    op.create_table(
        'user_api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('encryption_nonce', sa.Text(), nullable=False),
        sa.Column('key_hint', sa.String(length=8), nullable=False),
        sa.Column('is_valid', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='uq_user_provider'),
        sa.CheckConstraint("provider IN ('openai', 'google', 'anthropic')", name='ck_valid_provider'),
    )
    op.create_index('idx_user_api_keys_user_id', 'user_api_keys', ['user_id'])

    # Add preference columns to user_settings
    op.add_column('user_settings', sa.Column('preferred_provider', sa.String(length=20), nullable=True))
    op.add_column('user_settings', sa.Column('preferred_model', sa.String(length=100), nullable=True))
    op.create_check_constraint(
        'chk_user_settings_valid_preferred_provider',
        'user_settings',
        "preferred_provider IS NULL OR preferred_provider IN ('openai', 'google', 'anthropic')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('chk_user_settings_valid_preferred_provider', 'user_settings', type_='check')
    op.drop_column('user_settings', 'preferred_model')
    op.drop_column('user_settings', 'preferred_provider')
    op.drop_index('idx_user_api_keys_user_id', table_name='user_api_keys')
    op.drop_table('user_api_keys')
