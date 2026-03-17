"""Diet API Pydantic schemas"""

# Import all schemas for easy access
from app.schemas.diet import (
    UserSettingsIn,
    UserSettingsOut,
    DietSummary,
    TipoPasto,
    PastoSchema,
    DietaSettimanaleSchema,
    DietaConLista,
    RecipeResponse,
    ModifyDietRequest
)
from baml_client.types import Ingrediente
from app.schemas.saved_recipe import (
    SavedRecipeCreate,
    SavedRecipeOut
)

# Export all schemas
__all__ = [
    "UserSettingsIn",
    "UserSettingsOut",
    "DietSummary",
    "TipoPasto",
    "Ingrediente",
    "PastoSchema",
    "DietaSettimanaleSchema",
    "DietaConLista",
    "RecipeResponse",
    "ModifyDietRequest",
    "SavedRecipeCreate",
    "SavedRecipeOut"
]