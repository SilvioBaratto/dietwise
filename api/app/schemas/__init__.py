"""Diet API Pydantic schemas"""

# Import all schemas for easy access
from app.schemas.api_key import (
    ApiKeyResponseSchema,
    ApiKeySaveRequest,
    AvailableModelsResponse,
    ProviderPreferencesRequest,
    ProviderPreferencesResponse,
    ValidateKeyRequest,
    ValidateKeyResponse,
)
from app.schemas.diet import (
    DietaConLista,
    DietaSettimanaleSchema,
    DietSummary,
    ModifyDietRequest,
    PastoSchema,
    RecipeResponse,
    TipoPasto,
    UserSettingsIn,
    UserSettingsOut,
)
from app.schemas.saved_recipe import SavedRecipeCreate, SavedRecipeOut
from baml_client.types import Ingrediente

# Export all schemas
__all__ = [
    "ApiKeyResponseSchema",
    "ApiKeySaveRequest",
    "AvailableModelsResponse",
    "ProviderPreferencesRequest",
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
    "SavedRecipeOut",
    "ProviderPreferencesResponse",
    "ValidateKeyRequest",
    "ValidateKeyResponse",
]
