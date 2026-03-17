"""Diet-related Pydantic schemas"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from baml_client.types import (
    Ingrediente,
    HtmlStructure,
    TipoPasto as TipoPastoEnum,
    GiornoSettimana
)


class TipoPasto(BaseModel):
    """Schema for meal type information"""

    tipo: TipoPastoEnum
    orario: Optional[str] = None
    ricetta: str


class UserSettingsIn(BaseModel):
    """Input schema for user settings"""

    model_config = ConfigDict(from_attributes=True)

    age: Optional[int] = None  # years
    sex: Optional[str] = None  # 'M' or 'F'
    weight: Optional[float] = None  # kg
    height: Optional[float] = None  # cm
    other_data: Optional[str] = None
    goals: Optional[str] = None


class UserSettingsOut(UserSettingsIn):
    """Output schema for user settings"""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class DietSummary(BaseModel):
    """Summary schema for diet listing"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: Optional[str] = None
    created_at: datetime


class PastoSchema(BaseModel):
    """Schema for individual meal/pasto"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tipoPasto: TipoPasto
    ingredienti: str  # Comma-separated ingredient string (e.g., "avena 50g, latte 200ml, banana 1pz")
    calorie: int
    day: GiornoSettimana


class DietaSettimanaleSchema(BaseModel):
    """Schema for weekly diet plan"""

    id: str  # Diet ID for subsequent operations (e.g., generating grocery list)
    nome: str
    dataInizio: str
    dataFine: str
    pasti: List[PastoSchema]


class DietaConLista(BaseModel):
    """Schema for diet with grocery list"""

    dieta: DietaSettimanaleSchema
    listaSpesa: "ListaSpesaSchema"


class RecipeResponse(BaseModel):
    """Schema for recipe response"""

    recipe: HtmlStructure


class ModifyDietRequest(BaseModel):
    """Request schema for modifying an existing diet"""

    modification_prompt: str  # User's request for modifications (e.g., "Replace breakfast on Monday with something without eggs")


# Import ListaSpesaSchema from baml_client
from baml_client.types import ListaSpesa as ListaSpesaSchema

# Update the forward reference
DietaConLista.model_rebuild()
