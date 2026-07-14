"""add missing check constraints on meals weekly_diets ingredients

Revision ID: f7c2d2e1cc98
Revises: ff39b099730f
Create Date: 2026-07-14 21:44:50.587982

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7c2d2e1cc98"
down_revision: Union[str, Sequence[str], None] = "ff39b099730f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Same gap as ff39b099730f: these have been declared on the models since
    # their tables were created, but autogenerate doesn't detect CHECK
    # constraints, so they were never actually applied to the database.
    op.create_check_constraint(
        "chk_weekly_diets_date_range", "weekly_diets", "start_date < end_date"
    )
    op.create_check_constraint("chk_meals_positive_calories", "meals", "calories >= 0")
    op.create_check_constraint("chk_meals_positive_proteine", "meals", "proteine >= 0")
    op.create_check_constraint(
        "chk_meals_positive_carboidrati", "meals", "carboidrati >= 0"
    )
    op.create_check_constraint("chk_meals_positive_grassi", "meals", "grassi >= 0")
    op.create_check_constraint(
        "chk_ingredients_non_empty_name", "ingredients", "name != ''"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("chk_ingredients_non_empty_name", "ingredients", type_="check")
    op.drop_constraint("chk_meals_positive_grassi", "meals", type_="check")
    op.drop_constraint("chk_meals_positive_carboidrati", "meals", type_="check")
    op.drop_constraint("chk_meals_positive_proteine", "meals", type_="check")
    op.drop_constraint("chk_meals_positive_calories", "meals", type_="check")
    op.drop_constraint("chk_weekly_diets_date_range", "weekly_diets", type_="check")
