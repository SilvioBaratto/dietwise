"""add missing positive quantity check constraint on grocery_list_items

Revision ID: ff39b099730f
Revises: 0d196d12cd57
Create Date: 2026-07-14 21:41:49.184356

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff39b099730f"
down_revision: Union[str, Sequence[str], None] = "0d196d12cd57"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Model has declared this constraint since grocery_list_items was created,
    # but autogenerate doesn't detect CHECK constraints — it was never
    # actually applied to the database. Backfill it here.
    op.create_check_constraint(
        "chk_grocery_list_items_positive_quantity",
        "grocery_list_items",
        "quantity > 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "chk_grocery_list_items_positive_quantity",
        "grocery_list_items",
        type_="check",
    )
