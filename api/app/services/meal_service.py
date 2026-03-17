"""Meal service for business logic operations"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.exceptions import ApiKeyNotConfiguredError, LLMProviderError, RateLimitError
from app.repositories import MealRepository
from app.schemas import PastoSchema
from app.schemas import TipoPasto as TipoPastoSchema
from app.services.baml_client_factory import BamlClientFactory
from baml_client.types import HtmlStructure
from baml_client.types import Pasto as PastoBAML

logger = logging.getLogger(__name__)


def convert_pasto_schema_to_baml(pasto: PastoSchema) -> PastoBAML:
    """Convert PastoSchema to BAML Pasto format"""
    return PastoBAML(
        giorno=pasto.day,
        tipo=pasto.tipoPasto.tipo,
        nome=pasto.tipoPasto.ricetta,
        orario=pasto.tipoPasto.orario or "",
        ingredienti=pasto.ingredienti,
        calorie=pasto.calorie,
        proteine=pasto.proteine,
        carboidrati=pasto.carboidrati,
        grassi=pasto.grassi,
    )


class MealService:
    """Service class for meal-related business logic"""

    def __init__(self, db: Session, user_id: str) -> None:
        self.db = db
        self.user_id = user_id
        self.meal_repo = MealRepository(db)
        self._baml = BamlClientFactory(db, user_id)

    def get_meal_details(self, meal_id: str, user_id: str) -> PastoSchema:
        """Get detailed meal information"""
        meal = self.meal_repo.get_with_ingredients(meal_id)

        if not meal:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Meal not found.")

        if meal.weekly_diet.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to that meal.")

        return PastoSchema(
            id=meal.id,
            tipoPasto=TipoPastoSchema(
                tipo=meal.meal_type,
                orario=meal.time,
                ricetta=meal.recipe or "",
            ),
            ingredienti=meal.ingredienti,
            calorie=meal.calories,
            proteine=meal.proteine,
            carboidrati=meal.carboidrati,
            grassi=meal.grassi,
            day=meal.day,
        )

    async def get_meal_recipe(self, meal_id: str, user_id: str) -> HtmlStructure:
        """Generate full recipe for a meal"""
        meal = self.meal_repo.get_with_ingredients(meal_id)

        if not meal:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Meal not found.")

        if meal.weekly_diet.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to that meal.")

        # Build BAML Pasto directly from meal
        pasto_baml = PastoBAML(
            giorno=meal.day,
            tipo=meal.meal_type,
            nome=meal.recipe or "",
            orario=meal.time,
            ingredienti=meal.ingredienti,
            calorie=meal.calories,
            proteine=meal.proteine,
            carboidrati=meal.carboidrati,
            grassi=meal.grassi,
        )

        try:
            full_recipe: HtmlStructure = await self._baml.get_client().GeneraRicetta(pasto_baml)
        except (ApiKeyNotConfiguredError, LLMProviderError, RateLimitError):
            raise
        except Exception as e:
            self._baml.handle_baml_error(e)

        return full_recipe
