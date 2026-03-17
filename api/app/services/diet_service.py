"""Diet service for business logic operations"""

from datetime import date
import logging
from typing import cast
import uuid

from fastapi import HTTPException, status
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.exceptions import ApiKeyNotConfiguredError, LLMProviderError, RateLimitError
from app.repositories import (
    DietRepository,
    GroceryListItemRepository,
    GroceryListRepository,
    IngredientRepository,
    MealRepository,
    UserSettingsRepository,
)
from app.schemas import DietaConLista, DietSummary
from app.schemas import Ingrediente as IngredienteSchema
from app.schemas import TipoPasto as TipoPastoSchema
from app.services.baml_client_factory import BamlClientFactory
from baml_client.types import ListaSpesa as ListaSpesaSchema

logger = logging.getLogger(__name__)


def get_baml_day_enum(date_obj: date) -> str:
    """Convert date to BAML GiornoSettimana enum value"""
    day_enums = {
        0: "LUNEDI",
        1: "MARTEDI",
        2: "MERCOLEDI",
        3: "GIOVEDI",
        4: "VENERDI",
        5: "SABATO",
        6: "DOMENICA"
    }
    return day_enums[date_obj.weekday()]


def _meal_to_schema(m):
    """Convert a Meal DB model to PastoSchema"""
    from app.schemas.diet import PastoSchema
    return PastoSchema(
        id=m.id,
        tipoPasto=TipoPastoSchema(
            tipo=m.meal_type,
            orario=m.time,
            ricetta=m.recipe or "",
        ),
        ingredienti=m.ingredienti,
        calorie=m.calories,
        proteine=m.proteine,
        carboidrati=m.carboidrati,
        grassi=m.grassi,
        day=m.day,
    )


def _meals_to_baml(meals):
    """Convert DB meals to flat list of BAML Pasto objects"""
    from baml_client.types import Pasto as PastoBAML
    return [
        PastoBAML(
            giorno=m.day,
            tipo=m.meal_type,
            nome=m.recipe or "",
            orario=m.time,
            ingredienti=m.ingredienti,
            calorie=m.calories,
            proteine=m.proteine,
            carboidrati=m.carboidrati,
            grassi=m.grassi,
        )
        for m in meals
    ]


class DietService:
    """Service class for diet-related business logic"""

    def __init__(self, db: Session, user_id: str) -> None:
        self.db = db
        self.user_id = user_id
        self.diet_repo = DietRepository(db)
        self.meal_repo = MealRepository(db)
        self.ingredient_repo = IngredientRepository(db)
        self.grocery_list_repo = GroceryListRepository(db)
        self.grocery_list_item_repo = GroceryListItemRepository(db)
        self.user_settings_repo = UserSettingsRepository(db)
        self._baml = BamlClientFactory(db, user_id)

    def get_user_diets(self, user_id: str) -> list[DietSummary]:
        """Get all diets for a user"""
        diets = self.diet_repo.get_user_diets(user_id)
        return [
            DietSummary(
                id=diet.id,
                name=diet.name,
                created_at=diet.created_at
            )
            for diet in diets
        ]

    def get_diet_by_id(self, diet_id: str, user_id: str):
        """Get full diet by ID"""
        from app.schemas.diet import DietaSettimanaleSchema

        weekly = self.diet_repo.get_with_meals(diet_id, user_id)

        if not weekly:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet not found."
            )

        return DietaSettimanaleSchema(
            id=weekly.id,
            nome=weekly.name,
            dataInizio=weekly.start_date.isoformat(),
            dataFine=weekly.end_date.isoformat(),
            pasti=[_meal_to_schema(m) for m in weekly.meals],
        )

    async def create_diet(self, user_id: str):
        """Create a new weekly diet WITHOUT grocery list (Step 1 of 2)"""
        from datetime import timedelta

        from app.schemas.diet import DietaSettimanaleSchema

        # Load user settings
        settings = self.user_settings_repo.get_by_user_id(user_id)
        if not settings:
            raise HTTPException(404, "User settings not found.")
        if settings.weight is None or settings.height is None:
            raise HTTPException(400, "Weight and height must be set.")

        # Calculate dates: from today until next Sunday (or this Sunday if today is Sunday)
        today = date.today()
        # weekday(): Monday=0, Sunday=6
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            # Today is Sunday - generate until next Sunday (7 days)
            end_date = today + timedelta(days=7)
        else:
            # Generate from today until this week's Sunday
            end_date = today + timedelta(days=days_until_sunday)

        # Generate diet using BAML (Step 1 - only diet, no grocery list)
        try:
            external = await self._baml.get_client().GeneraDietaSettimanale(
                dataInizio=today.isoformat(),
                giornoInizio=get_baml_day_enum(today),
                dataFine=end_date.isoformat(),
                giornoFine=get_baml_day_enum(end_date),
                peso=settings.weight,
                altezza=settings.height,
                eta=settings.age,
                sesso=settings.sex,
                obiettivo=settings.goals or "",
                altri_dati=settings.other_data or "",
            )
        except (ApiKeyNotConfiguredError, LLMProviderError, RateLimitError):
            raise
        except Exception as e:
            self._baml.handle_baml_error(e)

        # Save WeeklyDiet with calculated dates (today until Sunday)
        weekly = self.diet_repo.create_diet(
            user_id=user_id,
            diet_id=str(uuid.uuid4()),
            start_date=today,
            end_date=end_date,
            name=external.nome,
        )

        # Iterate over flat pasti list (each pasto includes its giorno)
        for pasto in external.pasti:
            self.meal_repo.create_meal(
                meal_id=str(uuid.uuid4()),
                weekly_diet_id=weekly.id,
                meal_type=pasto.tipo,
                day=pasto.giorno,
                time=pasto.orario,
                recipe=pasto.nome,
                calories=pasto.calorie,
                ingredienti=pasto.ingredienti,
                proteine=pasto.proteine,
                carboidrati=pasto.carboidrati,
                grassi=pasto.grassi,
            )

        # Commit all changes
        self.db.commit()

        # Reload saved data
        saved = self.diet_repo.get_with_meals(weekly.id, user_id)

        if not saved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload created diet"
            )

        return DietaSettimanaleSchema(
            id=saved.id,
            nome=saved.name,
            dataInizio=saved.start_date.isoformat(),
            dataFine=saved.end_date.isoformat(),
            pasti=[_meal_to_schema(m) for m in saved.meals],
        )

    async def create_grocery_list_for_diet(self, diet_id: str, user_id: str) -> ListaSpesaSchema:
        """Generate and save grocery list for an existing diet (Step 2 of 2)"""
        # Verify diet exists and belongs to user
        weekly = self.diet_repo.get_with_meals(diet_id, user_id)
        if not weekly:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet not found."
            )

        # Check if grocery list already exists
        if weekly.grocery_list and weekly.grocery_list.items:
            logger.info(f"Grocery list already exists for diet {diet_id}, returning existing list")
            items = [
                IngredienteSchema(
                    nome=gi.ingredient.name,
                    quantita=gi.quantity,
                    unita=gi.ingredient.unit
                )
                for gi in weekly.grocery_list.items
            ]
            return ListaSpesaSchema(ingredienti=items)

        # Build flat BAML Pasto list (TOON-friendly) — no more grouping by day
        pasti_baml = _meals_to_baml(weekly.meals)

        # Generate grocery list using BAML (uses TOON format in prompt)
        try:
            grocery = await self._baml.get_client().GeneraListaSpesa(pasti_baml)
        except (ApiKeyNotConfiguredError, LLMProviderError, RateLimitError):
            raise
        except Exception as e:
            self._baml.handle_baml_error(e)

        # Save grocery list
        grocery_list = self.grocery_list_repo.create_grocery_list(
            grocery_list_id=str(uuid.uuid4()),
            weekly_diet_id=weekly.id
        )

        for ingr in grocery.ingredienti:
            existing_ingr = self.ingredient_repo.get_by_name(ingr.nome)

            if not existing_ingr:
                existing_ingr = self.ingredient_repo.create_ingredient(
                    ingredient_id=str(uuid.uuid4()),
                    name=ingr.nome,
                    unit=ingr.unita,
                )

            self.grocery_list_item_repo.create_grocery_item(
                item_id=str(uuid.uuid4()),
                grocery_list_id=grocery_list.id,
                ingredient_id=existing_ingr.id,
                quantity=ingr.quantita,
            )

        # Commit changes
        self.db.commit()

        return ListaSpesaSchema(
            ingredienti=[
                IngredienteSchema(
                    nome=ingr.nome,
                    quantita=ingr.quantita,
                    unita=ingr.unita
                )
                for ingr in grocery.ingredienti
            ]
        )

    def get_current_week_diet(self, user_id: str) -> DietaConLista | None:
        """Get current week's diet with grocery list. Returns None if no diet exists."""
        today = date.today()
        logger.debug(f"Looking for diet for user {user_id} on date {today}")
        weekly = self.diet_repo.get_current_week_diet(user_id, today)

        if not weekly:
            all_diets = self.diet_repo.get_user_diets(user_id)
            logger.debug(f"User has {len(all_diets)} total diets")
            for diet in all_diets:
                logger.debug(f"Diet {diet.id}: {diet.start_date} to {diet.end_date}")

            logger.info(f"No diet found for user {user_id} for the current week - this is normal")
            return None

        # Build grocery list
        items: list[IngredienteSchema] = []
        if weekly.grocery_list and weekly.grocery_list.items:
            for gi in weekly.grocery_list.items:
                items.append(
                    IngredienteSchema(
                        nome=gi.ingredient.name,
                        quantita=gi.quantity,
                        unita=gi.ingredient.unit,
                    )
                )

        from app.schemas.diet import DietaSettimanaleSchema
        return DietaConLista(
            dieta=DietaSettimanaleSchema(
                id=weekly.id,
                nome=weekly.name,
                dataInizio=weekly.start_date.isoformat(),
                dataFine=weekly.end_date.isoformat(),
                pasti=[_meal_to_schema(m) for m in weekly.meals],
            ),
            listaSpesa=ListaSpesaSchema(ingredienti=items),
        )

    def get_grocery_list_by_diet_id(self, diet_id: str, user_id: str) -> ListaSpesaSchema:
        """Get grocery list for a specific diet by ID"""
        weekly = self.diet_repo.get_with_grocery_list(diet_id, user_id)

        if not weekly:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet not found."
            )

        if not weekly.grocery_list or not weekly.grocery_list.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No grocery list found for this diet."
            )

        items = []
        for gi in weekly.grocery_list.items:
            items.append(
                IngredienteSchema(
                    nome=gi.ingredient.name,
                    quantita=gi.quantity,
                    unita=gi.ingredient.unit
                )
            )

        return ListaSpesaSchema(ingredienti=items)

    async def modify_diet(self, diet_id: str, user_id: str, modification_prompt: str):
        """Modify an existing diet based on user's prompt using LLM"""
        from app.schemas.diet import DietaSettimanaleSchema
        from baml_client.types import DietaSettimanale as DietaSettimanaleBAML

        # Load user settings
        settings = self.user_settings_repo.get_by_user_id(user_id)
        if not settings:
            raise HTTPException(404, "User settings not found.")
        if settings.weight is None or settings.height is None:
            raise HTTPException(400, "Weight and height must be set.")

        # Get existing diet
        weekly = self.diet_repo.get_with_meals(diet_id, user_id)
        if not weekly:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet not found."
            )

        # Build flat BAML representation (TOON-friendly)
        current_diet_baml = DietaSettimanaleBAML(
            nome=weekly.name,
            dataInizio=weekly.start_date.isoformat(),
            dataFine=weekly.end_date.isoformat(),
            pasti=_meals_to_baml(weekly.meals),
        )

        # Call BAML to modify the diet
        try:
            today = date.today()
            modified = await self._baml.get_client().ModificaDietaSettimanale(
                dietaCorrente=current_diet_baml,
                richiestaModifica=modification_prompt,
                peso=settings.weight,
                altezza=settings.height,
                eta=settings.age,
                sesso=settings.sex,
                obiettivo=settings.goals or "",
                oggiData=today.isoformat(),
                oggiGiorno=get_baml_day_enum(today),
            )
        except (ApiKeyNotConfiguredError, LLMProviderError, RateLimitError):
            raise
        except Exception as e:
            self._baml.handle_baml_error(e)

        # Delete existing meals for this diet
        from sqlalchemy import delete as sql_delete

        from app.models import Meal

        stmt = sql_delete(Meal).where(Meal.weekly_diet_id == weekly.id)
        self.db.execute(stmt)
        self.db.flush()

        # Update diet name and dates if changed
        weekly.name = modified.nome
        weekly.start_date = date.fromisoformat(modified.dataInizio)
        weekly.end_date = date.fromisoformat(modified.dataFine)

        # Save new meals from flat pasti list
        for pasto in modified.pasti:
            self.meal_repo.create_meal(
                meal_id=str(uuid.uuid4()),
                weekly_diet_id=weekly.id,
                meal_type=pasto.tipo,
                day=pasto.giorno,
                time=pasto.orario,
                recipe=pasto.nome,
                calories=pasto.calorie,
                ingredienti=pasto.ingredienti,
                proteine=pasto.proteine,
                carboidrati=pasto.carboidrati,
                grassi=pasto.grassi,
            )

        # Delete existing grocery list if it exists
        if weekly.grocery_list:
            from app.models import GroceryList
            stmt = sql_delete(GroceryList).where(GroceryList.weekly_diet_id == weekly.id)
            self.db.execute(stmt)
            self.db.flush()

        # Commit meal changes
        self.db.commit()

        # Reload saved data with meals
        saved = self.diet_repo.get_with_meals(weekly.id, user_id)

        if not saved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload modified diet"
            )

        # Generate new grocery list from flat pasti (TOON-friendly)
        pasti_baml = _meals_to_baml(saved.meals)

        try:
            grocery = await self._baml.get_client().GeneraListaSpesa(pasti_baml)
        except (ApiKeyNotConfiguredError, LLMProviderError, RateLimitError):
            raise
        except Exception as e:
            self._baml.handle_baml_error(e)

        # Save grocery list
        grocery_list = self.grocery_list_repo.create_grocery_list(
            grocery_list_id=str(uuid.uuid4()),
            weekly_diet_id=saved.id
        )

        for ingr in grocery.ingredienti:
            existing_ingr = self.ingredient_repo.get_by_name(ingr.nome)

            if not existing_ingr:
                existing_ingr = self.ingredient_repo.create_ingredient(
                    ingredient_id=str(uuid.uuid4()),
                    name=ingr.nome,
                    unit=ingr.unita,
                )

            self.grocery_list_item_repo.create_grocery_item(
                item_id=str(uuid.uuid4()),
                grocery_list_id=grocery_list.id,
                ingredient_id=existing_ingr.id,
                quantity=ingr.quantita,
            )

        # Commit grocery list changes
        self.db.commit()

        grocery_items = [
            IngredienteSchema(
                nome=ingr.nome,
                quantita=ingr.quantita,
                unita=ingr.unita
            )
            for ingr in grocery.ingredienti
        ]

        return DietaConLista(
            dieta=DietaSettimanaleSchema(
                id=saved.id,
                nome=saved.name,
                dataInizio=saved.start_date.isoformat(),
                dataFine=saved.end_date.isoformat(),
                pasti=[_meal_to_schema(m) for m in saved.meals],
            ),
            listaSpesa=ListaSpesaSchema(ingredienti=grocery_items)
        )

    def delete_diet(self, diet_id: str, user_id: str) -> bool:
        """Delete a weekly diet plan"""
        from sqlalchemy import delete as sql_delete

        from app.models import WeeklyDiet

        stmt = (
            sql_delete(WeeklyDiet)
            .where(WeeklyDiet.id == diet_id, WeeklyDiet.user_id == user_id)
        )

        result = self.db.execute(stmt)
        rows_deleted = cast(CursorResult, result).rowcount

        if rows_deleted == 0:
            weekly = self.diet_repo.get(diet_id)
            if not weekly:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Diet not found."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this diet."
                )

        self.db.commit()
        logger.info(f"Deleted diet {diet_id} for user {user_id}")
        return True
