"""Meal service for business logic operations"""

import logging

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories import MealRepository
from app.schemas import PastoSchema, TipoPasto as TipoPastoSchema
from baml_client.async_client import b
from baml_client.types import HtmlStructure, Pasto as PastoBAML

logger = logging.getLogger(__name__)


def convert_pasto_schema_to_baml(pasto: PastoSchema) -> PastoBAML:
    """Convert PastoSchema to BAML Pasto format"""
    return PastoBAML(
        tipo=pasto.tipoPasto.tipo,
        nome=pasto.tipoPasto.ricetta,
        orario=pasto.tipoPasto.orario or "",
        ingredienti=pasto.ingredienti,  # Already a string
        calorie=pasto.calorie
    )


class MealService:
    """Service class for meal-related business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.meal_repo = MealRepository(db)
    
    def get_meal_details(self, meal_id: str, user_id: str) -> PastoSchema:
        """Get detailed meal information"""
        meal = self.meal_repo.get_with_ingredients(meal_id)

        if not meal:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Meal not found.")

        # Ensure it belongs to the current user
        if meal.weekly_diet.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to that meal.")

        return PastoSchema(
            id=meal.id,
            tipoPasto=TipoPastoSchema(
                tipo=meal.meal_type,  # Direct BAML enum
                orario=meal.time,
                ricetta=meal.recipe or "",
            ),
            ingredienti=meal.ingredienti,  # Direct string
            calorie=meal.calories,
            day=meal.day,  # Direct BAML enum
        )
    
    async def get_meal_recipe(self, meal_id: str, user_id: str) -> HtmlStructure:
        """Generate full recipe for a meal"""
        meal = self.meal_repo.get_with_ingredients(meal_id)

        if not meal:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Meal not found.")

        if meal.weekly_diet.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to that meal.")

        # Build PastoSchema directly from meal using BAML enums
        pasto = PastoSchema(
            id=meal.id,
            tipoPasto=TipoPastoSchema(
                tipo=meal.meal_type,  # Direct BAML enum
                orario=meal.time,
                ricetta=meal.recipe or "",
            ),
            ingredienti=meal.ingredienti,  # Direct string
            calorie=meal.calories,
            day=meal.day,  # Direct BAML enum
        )

        # Convert PastoSchema to BAML Pasto format
        pasto_baml = convert_pasto_schema_to_baml(pasto)

        try:
            full_recipe: HtmlStructure = await b.GeneraRicetta(pasto_baml)
        except Exception as e:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                f"Failed to generate recipe: {e}"
            )

        return full_recipe