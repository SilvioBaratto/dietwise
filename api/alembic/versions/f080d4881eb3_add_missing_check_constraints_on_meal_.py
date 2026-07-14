"""add missing check constraints on meal_ingredients and user_settings

Revision ID: f080d4881eb3
Revises: f7c2d2e1cc98
Create Date: 2026-07-14 21:47:41.874078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f080d4881eb3'
down_revision: Union[str, Sequence[str], None] = 'f7c2d2e1cc98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Same gap as ff39b099730f / f7c2d2e1cc98: declared on the models,
    # never applied since autogenerate doesn't detect CHECK constraints.
    op.create_check_constraint(
        "chk_meal_ingredients_positive_quantity", "meal_ingredients", "quantity > 0"
    )
    op.create_check_constraint(
        "chk_user_settings_valid_age",
        "user_settings",
        "age IS NULL OR (age > 0 AND age < 150)",
    )
    op.create_check_constraint(
        "chk_user_settings_positive_weight",
        "user_settings",
        "weight IS NULL OR weight > 0",
    )
    op.create_check_constraint(
        "chk_user_settings_positive_height",
        "user_settings",
        "height IS NULL OR height > 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("chk_user_settings_positive_height", "user_settings", type_="check")
    op.drop_constraint("chk_user_settings_positive_weight", "user_settings", type_="check")
    op.drop_constraint("chk_user_settings_valid_age", "user_settings", type_="check")
    op.drop_constraint("chk_meal_ingredients_positive_quantity", "meal_ingredients", type_="check")
