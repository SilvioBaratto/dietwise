"""Meal API endpoints"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.schemas import PastoSchema, RecipeResponse
from app.services import MealService

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get(
    "/{meal_id}",
    response_model=PastoSchema,
    summary="Retrieve the details of a single meal by its ID",
)
def get_meal_details(
    meal_id: str = Path(..., description="The UUID of the meal"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get detailed information about a specific meal"""
    user_id = current_user["id"]
    meal_service = MealService(db, user_id)
    return meal_service.get_meal_details(meal_id, user_id)


@router.get(
    "/{meal_id}/recipe",
    response_model=RecipeResponse,
    summary="Get the prepared recipe text for a given meal",
)
async def get_meal_recipe(
    meal_id: str = Path(..., description="UUID of the meal"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a full recipe for the specified meal"""
    user_id = current_user["id"]
    meal_service = MealService(db, user_id)
    recipe = await meal_service.get_meal_recipe(meal_id, user_id)
    return RecipeResponse(recipe=recipe)
