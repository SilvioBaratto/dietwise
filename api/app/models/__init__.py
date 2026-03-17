"""Database models for Diet API"""

# Import base classes
from app.models.base import Base

# Import all models for easy access
from app.models.diet import (
    User,
    WeeklyDiet,
    Meal,
    Ingredient,
    MealIngredient,
    GroceryList,
    GroceryListItem,
    SavedRecipe,
    UserSettings,
)

# Import BAML enums for convenience
from baml_client.types import TipoPasto, GiornoSettimana, UnitaMisura

# Export all models and enums
__all__ = [
    "Base",
    "User",
    "WeeklyDiet",
    "Meal",
    "Ingredient",
    "MealIngredient",
    "GroceryList",
    "GroceryListItem",
    "SavedRecipe",
    "UserSettings",
    "TipoPasto",
    "GiornoSettimana",
    "UnitaMisura",
]