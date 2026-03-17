"""Recipe API endpoints for saving and retrieving recipes"""

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.repositories import SavedRecipeRepository
from app.schemas import SavedRecipeCreate, SavedRecipeOut
from baml_client.types import TipoPasto

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post(
    "",
    response_model=SavedRecipeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Save a generated recipe",
)
def save_recipe(
    recipe_data: SavedRecipeCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Save an AI-generated recipe to the user's collection"""
    user_id = current_user["id"]
    recipe_repo = SavedRecipeRepository(db)

    # Map meal type string to BAML enum
    meal_type_map = {
        "colazione": TipoPasto.COLAZIONE,
        "spuntino_mattina": TipoPasto.SPUNTINO_MATTINA,
        "pranzo": TipoPasto.PRANZO,
        "spuntino_pomeriggio": TipoPasto.SPUNTINO_POMERIGGIO,
        "cena": TipoPasto.CENA,
    }
    meal_type_enum = meal_type_map.get(recipe_data.meal_type.lower())

    if not meal_type_enum:
        raise HTTPException(400, f"Invalid meal type: {recipe_data.meal_type}")

    saved_recipe = recipe_repo.create_saved_recipe(
        recipe_id=str(uuid.uuid4()),
        user_id=user_id,
        recipe_name=recipe_data.recipe_name,
        recipe_instructions=recipe_data.recipe_instructions,
        meal_type=meal_type_enum,
        calories=recipe_data.calories
    )

    db.commit()
    db.refresh(saved_recipe)

    return SavedRecipeOut(
        id=saved_recipe.id,
        recipe_name=saved_recipe.recipe_name,
        recipe_instructions=saved_recipe.recipe_instructions,
        meal_type=saved_recipe.meal_type.value,
        calories=saved_recipe.calories,
        created_at=saved_recipe.created_at
    )


@router.get(
    "",
    response_model=list[SavedRecipeOut],
    summary="Get all saved recipes for the current user",
)
def get_user_recipes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve all saved recipes for the authenticated user"""
    user_id = current_user["id"]
    recipe_repo = SavedRecipeRepository(db)

    saved_recipes = recipe_repo.get_user_recipes(user_id)

    return [
        SavedRecipeOut(
            id=recipe.id,
            recipe_name=recipe.recipe_name,
            recipe_instructions=recipe.recipe_instructions,
            meal_type=recipe.meal_type.value,  # BAML enum .value
            calories=recipe.calories,
            created_at=recipe.created_at
        )
        for recipe in saved_recipes
    ]


@router.get(
    "/by-name/{recipe_name}",
    response_model=list[SavedRecipeOut],
    summary="Get saved recipes by recipe name",
)
def get_recipes_by_name(
    recipe_name: str = Path(..., description="Name of the recipe"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all saved versions of a specific recipe by name"""
    user_id = current_user["id"]
    recipe_repo = SavedRecipeRepository(db)

    saved_recipes = recipe_repo.get_by_recipe_name(recipe_name, user_id)

    return [
        SavedRecipeOut(
            id=recipe.id,
            recipe_name=recipe.recipe_name,
            recipe_instructions=recipe.recipe_instructions,
            meal_type=recipe.meal_type.value,  # BAML enum .value
            calories=recipe.calories,
            created_at=recipe.created_at
        )
        for recipe in saved_recipes
    ]


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved recipe",
)
def delete_recipe(
    recipe_id: str = Path(..., description="UUID of the saved recipe"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a saved recipe (only owner can delete)"""
    user_id = current_user["id"]
    recipe_repo = SavedRecipeRepository(db)

    # Get the recipe to verify ownership
    saved_recipe = recipe_repo.get(recipe_id)

    if not saved_recipe:
        raise HTTPException(404, "Recipe not found")

    if saved_recipe.user_id != user_id:
        raise HTTPException(403, "Not authorized to delete this recipe")

    recipe_repo.delete(recipe_id)
    db.commit()

    return None
