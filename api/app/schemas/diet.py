"""Diet-related Pydantic schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from baml_client.types import GiornoSettimana, HtmlStructure
from baml_client.types import ListaSpesa as ListaSpesaSchema
from baml_client.types import TipoPasto as TipoPastoEnum


class TipoPasto(BaseModel):
    """Schema for meal type information"""

    tipo: TipoPastoEnum
    orario: str | None = None
    ricetta: str


class UserSettingsIn(BaseModel):
    """Input schema for user settings"""

    model_config = ConfigDict(from_attributes=True)

    age: int | None = None  # years
    sex: str | None = None  # 'M' or 'F'
    weight: float | None = None  # kg
    height: float | None = None  # cm
    other_data: str | None = None
    goals: str | None = None


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
    name: str | None = None
    created_at: datetime


class PastoSchema(BaseModel):
    """Schema for individual meal/pasto"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tipoPasto: TipoPasto
    ingredienti: str  # Comma-separated ingredient string (e.g., "avena 50g, latte 200ml, banana 1pz")
    calorie: int
    proteine: int = 0
    carboidrati: int = 0
    grassi: int = 0
    day: GiornoSettimana


class DietaSettimanaleSchema(BaseModel):
    """Schema for weekly diet plan"""

    id: str  # Diet ID for subsequent operations (e.g., generating grocery list)
    nome: str
    dataInizio: str
    dataFine: str
    pasti: list[PastoSchema]


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


# Update the forward reference
DietaConLista.model_rebuild()
