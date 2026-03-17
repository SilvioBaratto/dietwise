"""Diet API endpoints"""

from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.services import DietService
from app.schemas import DietSummary, DietaConLista, ModifyDietRequest
from app.schemas.diet import DietaSettimanaleSchema
from baml_client.types import ListaSpesa as ListaSpesaSchema

router = APIRouter(prefix="/diet", tags=["diet"])


@router.get(
    "/list",
    response_model=List[DietSummary],
    summary="List all weekly diets for the current user",
)
def list_user_diets(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all diets for the current user"""
    user_id = current_user["id"]
    diet_service = DietService(db)
    return diet_service.get_user_diets(user_id)


@router.get(
    "/current_week",
    response_model=DietaConLista,
    summary="Retrieve the weekly diet plan + grocery list for the current week",
)
def get_current_week_diet(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get the diet plan for the current week"""
    user_id = current_user["id"]
    diet_service = DietService(db)
    result = diet_service.get_current_week_diet(user_id)

    # Return 404 if no diet exists for current week
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No diet found for the current week"
        )

    return result


@router.post(
    "/create_diet",
    response_model=DietaSettimanaleSchema,
    summary="Generate and save a weekly diet plan (Step 1 of 2 - without grocery list)",
)
async def create_diet(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new weekly diet plan WITHOUT grocery list. Call POST /diet/{diet_id}/grocery-list next to generate the shopping list."""
    user_id = current_user["id"]
    diet_service = DietService(db)
    return await diet_service.create_diet(user_id)


@router.post(
    "/{diet_id}/grocery-list",
    response_model=ListaSpesaSchema,
    summary="Generate and save grocery list for an existing diet (Step 2 of 2)",
)
async def create_grocery_list(
    diet_id: str = Path(..., description="The UUID of the weekly diet"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate grocery list for an existing diet. This is Step 2 after creating the diet."""
    user_id = current_user["id"]
    diet_service = DietService(db)
    return await diet_service.create_grocery_list_for_diet(diet_id, user_id)


@router.get(
    "/{diet_id}",
    response_model=DietaSettimanaleSchema,
    summary="Retrieve a full weekly diet by its ID (no shopping list)",
)
def get_diet_by_id(
    diet_id: str = Path(..., description="The UUID of the weekly diet"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific diet by ID"""
    user_id = current_user["id"]
    diet_service = DietService(db)
    return diet_service.get_diet_by_id(diet_id, user_id)


@router.get(
    "/{diet_id}/grocery-list",
    response_model=ListaSpesaSchema,
    summary="Retrieve the grocery list for a specific diet",
)
def get_diet_grocery_list(
    diet_id: str = Path(..., description="The UUID of the weekly diet"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get grocery list with ingredients, quantities, and units for a specific diet"""
    user_id = current_user["id"]
    diet_service = DietService(db)
    return diet_service.get_grocery_list_by_diet_id(diet_id, user_id)


@router.patch(
    "/{diet_id}/modify",
    response_model=DietaConLista,
    summary="Modify an existing diet based on user feedback",
)
async def modify_diet(
    request: ModifyDietRequest,
    diet_id: str = Path(..., description="The UUID of the weekly diet to modify"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Modify an existing diet using LLM based on user's modification request.

    Examples of modification prompts:
    - "Replace breakfast on Monday with something without eggs"
    - "I want more protein in my dinners"
    - "Change all snacks to fruit-based options"
    - "Make the diet more Mediterranean-style"

    This updates the existing diet instead of creating a new one.
    The grocery list is automatically regenerated based on the modified meals.
    """
    user_id = current_user["id"]
    diet_service = DietService(db)
    return await diet_service.modify_diet(diet_id, user_id, request.modification_prompt)


@router.delete(
    "/{diet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a weekly diet plan",
)
def delete_diet(
    diet_id: str = Path(..., description="The UUID of the weekly diet to delete"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a specific diet by ID. Only the owner can delete their diet."""
    user_id = current_user["id"]
    diet_service = DietService(db)
    diet_service.delete_diet(diet_id, user_id)
    return None