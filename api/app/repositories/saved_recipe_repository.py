"""Saved recipe repository for data access operations"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import SavedRecipe, TipoPasto
from app.repositories.base_repository import BaseRepository
from pydantic import BaseModel


class SavedRecipeCreate(BaseModel):
    """Schema for creating a saved recipe"""
    pass


class SavedRecipeRepository(BaseRepository[SavedRecipe, SavedRecipeCreate, SavedRecipeCreate]):
    """Repository for SavedRecipe operations"""

    def __init__(self, db: Session):
        super().__init__(SavedRecipe, db)

    def get_by_recipe_name(self, recipe_name: str, user_id: str) -> List[SavedRecipe]:
        """Get all saved recipes with a specific name for a user"""
        stmt = (
            select(SavedRecipe)
            .where(
                SavedRecipe.recipe_name == recipe_name,
                SavedRecipe.user_id == user_id
            )
            .order_by(SavedRecipe.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_user_recipes(self, user_id: str, meal_type: Optional[TipoPasto] = None) -> List[SavedRecipe]:
        """Get all saved recipes for a user, optionally filtered by meal type"""
        stmt = select(SavedRecipe).where(SavedRecipe.user_id == user_id)

        if meal_type:
            stmt = stmt.where(SavedRecipe.meal_type == meal_type)

        stmt = stmt.order_by(SavedRecipe.created_at.desc())

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def create_saved_recipe(
        self,
        recipe_id: str,
        user_id: str,
        recipe_name: str,
        recipe_instructions: str,
        meal_type: TipoPasto,
        calories: int
    ) -> SavedRecipe:
        """Create a new saved recipe"""
        saved_recipe = SavedRecipe(
            id=recipe_id,
            user_id=user_id,
            recipe_name=recipe_name,
            recipe_instructions=recipe_instructions,
            meal_type=meal_type,
            calories=calories
        )
        self.db.add(saved_recipe)
        self.db.flush()
        return saved_recipe
