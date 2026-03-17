"""Schemas for saved recipes"""

from pydantic import BaseModel
from datetime import datetime


class SavedRecipeCreate(BaseModel):
    """Schema for creating a saved recipe"""
    recipe_name: str
    recipe_instructions: str
    meal_type: str  # "breakfast", "lunch", "dinner", "snack"
    calories: int


class SavedRecipeOut(BaseModel):
    """Schema for returning a saved recipe"""
    id: str
    recipe_name: str
    recipe_instructions: str
    meal_type: str
    calories: int
    created_at: datetime

    class Config:
        from_attributes = True
