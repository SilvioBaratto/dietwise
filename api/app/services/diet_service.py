"""Diet service for business logic operations"""

import logging
import uuid
from datetime import date
from typing import List, cast

from sqlalchemy.orm import Session
from sqlalchemy.engine import CursorResult
from fastapi import HTTPException, status

from app.repositories import (
    DietRepository, MealRepository, IngredientRepository,
    GroceryListRepository, GroceryListItemRepository, UserSettingsRepository
)
from app.schemas import DietSummary, DietaConLista, TipoPasto as TipoPastoSchema, Ingrediente as IngredienteSchema
from baml_client.async_client import b
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


class DietService:
    """Service class for diet-related business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.diet_repo = DietRepository(db)
        self.meal_repo = MealRepository(db)
        self.ingredient_repo = IngredientRepository(db)
        self.grocery_list_repo = GroceryListRepository(db)
        self.grocery_list_item_repo = GroceryListItemRepository(db)
        self.user_settings_repo = UserSettingsRepository(db)
    
    def get_user_diets(self, user_id: str) -> List[DietSummary]:
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
        from app.schemas.diet import PastoSchema

        weekly = self.diet_repo.get_with_meals(diet_id, user_id)

        if not weekly:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diet not found."
            )

        # Build response using BAML enums directly
        pasti: List[PastoSchema] = []
        for m in weekly.meals:
            pasti.append(
                PastoSchema(
                    id=m.id,
                    tipoPasto=TipoPastoSchema(
                        tipo=m.meal_type,  # Direct BAML enum
                        orario=m.time,
                        ricetta=m.recipe or "",
                    ),
                    ingredienti=m.ingredienti,  # Just pass through the string
                    calorie=m.calories,
                    day=m.day,  # Direct BAML enum
                )
            )

        from app.schemas.diet import DietaSettimanaleSchema
        return DietaSettimanaleSchema(
            id=weekly.id,
            nome=weekly.name,
            dataInizio=weekly.start_date.isoformat(),
            dataFine=weekly.end_date.isoformat(),
            pasti=pasti,
        )
    
    async def create_diet(self, user_id: str):
        """Create a new weekly diet WITHOUT grocery list (Step 1 of 2)"""
        from app.schemas.diet import PastoSchema, DietaSettimanaleSchema
        from datetime import timedelta

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
            external = await b.GeneraDietaSettimanale(
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
        except Exception as e:
            logger.exception("Error generating diet")
            raise HTTPException(502, f"Generation failed: {e}")

        # Save WeeklyDiet with calculated dates (today until Sunday)
        weekly = self.diet_repo.create_diet(
            user_id=user_id,
            diet_id=str(uuid.uuid4()),
            start_date=today,
            end_date=end_date,
            name=external.nome,
        )

        # Iterate over each day in the weekly diet
        for giorno_dieta in external.dieta:
            # Process each meal for this day
            for pasto in giorno_dieta.pasti:
                self.meal_repo.create_meal(
                    meal_id=str(uuid.uuid4()),
                    weekly_diet_id=weekly.id,
                    meal_type=pasto.tipo,  # Direct BAML enum
                    day=giorno_dieta.giorno,  # Direct BAML enum
                    time=pasto.orario,
                    recipe=pasto.nome,
                    calories=pasto.calorie,
                    ingredienti=pasto.ingredienti,  # Store string directly
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

        # Build response using BAML enums directly
        response_meals: List[PastoSchema] = []
        logger.debug(f"Converting {len(saved.meals)} meals from database to API schema")
        for m in saved.meals:
            response_meals.append(
                PastoSchema(
                    id=m.id,
                    tipoPasto=TipoPastoSchema(
                        tipo=m.meal_type,  # Direct BAML enum
                        orario=m.time,
                        ricetta=m.recipe or "",
                    ),
                    ingredienti=m.ingredienti,  # Just pass through the string
                    calorie=m.calories,
                    day=m.day,  # Direct BAML enum
                )
            )

        return DietaSettimanaleSchema(
            id=saved.id,
            nome=saved.name,
            dataInizio=saved.start_date.isoformat(),
            dataFine=saved.end_date.isoformat(),
            pasti=response_meals,
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
                    unita=gi.ingredient.unit  # Direct BAML enum
                )
                for gi in weekly.grocery_list.items
            ]
            return ListaSpesaSchema(ingredienti=items)

        # Convert meals to BAML format grouped by day for grocery list generation
        from baml_client.types import Pasto as PastoBAML, Dieta as DietaBAML

        # Group meals by day
        meals_by_day = {}
        for m in weekly.meals:
            if m.day not in meals_by_day:
                meals_by_day[m.day] = []

            meals_by_day[m.day].append(PastoBAML(
                tipo=m.meal_type,  # Direct BAML enum
                nome=m.recipe or "",
                orario=m.time,  # Time from database
                ingredienti=m.ingredienti,  # Just use the string directly
                calorie=m.calories
            ))

        # Build Dieta objects for each day
        diete_baml = []
        for day in sorted(meals_by_day.keys()):
            diete_baml.append(DietaBAML(
                giorno=day,  # Direct BAML enum
                pasti=meals_by_day[day]
            ))

        # Generate grocery list using BAML
        try:
            grocery = await b.GeneraListaSpesa(diete_baml)
        except Exception as e:
            logger.exception("Error generating grocery list")
            raise HTTPException(502, f"Grocery list generation failed: {e}")

        # Save grocery list
        grocery_list = self.grocery_list_repo.create_grocery_list(
            grocery_list_id=str(uuid.uuid4()),
            weekly_diet_id=weekly.id
        )

        for ingr in grocery.ingredienti:
            existing_ingr = self.ingredient_repo.get_by_name(ingr.nome)

            # Create ingredient if it doesn't exist (same as diet creation logic)
            if not existing_ingr:
                existing_ingr = self.ingredient_repo.create_ingredient(
                    ingredient_id=str(uuid.uuid4()),
                    name=ingr.nome,
                    unit=ingr.unita,
                )

            # Create grocery list item
            self.grocery_list_item_repo.create_grocery_item(
                item_id=str(uuid.uuid4()),
                grocery_list_id=grocery_list.id,
                ingredient_id=existing_ingr.id,
                quantity=ingr.quantita,
            )

        # Commit changes
        self.db.commit()

        # Return the generated grocery list
        grocery_schema = ListaSpesaSchema(
            ingredienti=[
                IngredienteSchema(
                    nome=ingr.nome,
                    quantita=ingr.quantita,
                    unita=ingr.unita
                )
                for ingr in grocery.ingredienti
            ]
        )

        return grocery_schema
    
    def get_current_week_diet(self, user_id: str) -> DietaConLista | None:
        """Get current week's diet with grocery list. Returns None if no diet exists."""
        from app.schemas.diet import PastoSchema

        today = date.today()
        logger.debug(f"Looking for diet for user {user_id} on date {today}")
        weekly = self.diet_repo.get_current_week_diet(user_id, today)

        if not weekly:
            # Debug: check if user has any diets at all
            all_diets = self.diet_repo.get_user_diets(user_id)
            logger.debug(f"User has {len(all_diets)} total diets")
            for diet in all_diets:
                logger.debug(f"Diet {diet.id}: {diet.start_date} to {diet.end_date}")

            # Return None instead of raising an error - having no diet is a normal state
            logger.info(f"No diet found for user {user_id} for the current week - this is normal")
            return None

        # Build meals using BAML enums directly
        response_meals: List[PastoSchema] = []
        for m in weekly.meals:
            response_meals.append(
                PastoSchema(
                    id=m.id,
                    tipoPasto=TipoPastoSchema(
                        tipo=m.meal_type,  # Direct BAML enum
                        orario=m.time,
                        ricetta=m.recipe or "",
                    ),
                    ingredienti=m.ingredienti,  # Just pass through the string
                    calorie=m.calories,
                    day=m.day,  # Direct BAML enum
                )
            )

        # Build grocery list
        items: List[IngredienteSchema] = []
        if weekly.grocery_list and weekly.grocery_list.items:
            for gi in weekly.grocery_list.items:
                items.append(
                    IngredienteSchema(
                        nome=gi.ingredient.name,
                        quantita=gi.quantity,
                        unita=gi.ingredient.unit,  # Direct BAML enum
                    )
                )

        from app.schemas.diet import DietaSettimanaleSchema as DietaSettimanaleSchemaLocal2
        return DietaConLista(
            dieta=DietaSettimanaleSchemaLocal2(
                id=weekly.id,
                nome=weekly.name,
                dataInizio=weekly.start_date.isoformat(),
                dataFine=weekly.end_date.isoformat(),
                pasti=response_meals,
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

        # Build grocery list items
        items = []
        for gi in weekly.grocery_list.items:
            items.append(
                IngredienteSchema(
                    nome=gi.ingredient.name,
                    quantita=gi.quantity,
                    unita=gi.ingredient.unit  # Direct BAML enum
                )
            )

        return ListaSpesaSchema(ingredienti=items)

    async def modify_diet(self, diet_id: str, user_id: str, modification_prompt: str):
        """Modify an existing diet based on user's prompt using LLM"""
        from app.schemas.diet import PastoSchema, DietaSettimanaleSchema
        from baml_client.types import Pasto as PastoBAML, DietaSettimanale as DietaSettimanaleBAML

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

        # Convert existing diet to BAML format
        from baml_client.types import Dieta as DietaBAML

        # Group meals by day
        meals_by_day = {}
        for m in weekly.meals:
            if m.day not in meals_by_day:
                meals_by_day[m.day] = []

            # Ingredients are already stored as a comma-separated string
            meals_by_day[m.day].append(PastoBAML(
                tipo=m.meal_type,  # Direct BAML enum
                nome=m.recipe or "",
                orario=m.time,
                ingredienti=m.ingredienti,  # Just use the string directly
                calorie=m.calories
            ))

        # Build Dieta objects for each day
        diete_baml = []
        for day in sorted(meals_by_day.keys()):
            diete_baml.append(DietaBAML(
                giorno=day,  # Direct BAML enum
                pasti=meals_by_day[day]
            ))

        current_diet_baml = DietaSettimanaleBAML(
            nome=weekly.name,
            dataInizio=weekly.start_date.isoformat(),
            dataFine=weekly.end_date.isoformat(),
            dieta=diete_baml
        )

        # Call BAML to modify the diet
        try:
            today = date.today()
            modified = await b.ModificaDietaSettimanale(
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
        except Exception as e:
            logger.exception("Error modifying diet")
            raise HTTPException(502, f"Diet modification failed: {e}")

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

        # Save new meals (iterate over days)
        for giorno_dieta in modified.dieta:
            for pasto in giorno_dieta.pasti:
                self.meal_repo.create_meal(
                    meal_id=str(uuid.uuid4()),
                    weekly_diet_id=weekly.id,
                    meal_type=pasto.tipo,  # Direct BAML enum
                    day=giorno_dieta.giorno,  # Direct BAML enum
                    time=pasto.orario,
                    recipe=pasto.nome,
                    calories=pasto.calorie,
                    ingredienti=pasto.ingredienti,  # Store string directly
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

        # Generate new grocery list automatically
        from baml_client.types import Pasto as PastoBAML, Dieta as DietaBAML

        # Group meals by day for grocery list
        meals_by_day_grocery = {}
        for m in saved.meals:
            if m.day not in meals_by_day_grocery:
                meals_by_day_grocery[m.day] = []

            meals_by_day_grocery[m.day].append(PastoBAML(
                tipo=m.meal_type,  # Direct BAML enum
                nome=m.recipe or "",
                orario=m.time,  # Time from database
                ingredienti=m.ingredienti,  # Just use the string directly
                calorie=m.calories
            ))

        # Build Dieta objects for each day
        diete_baml_grocery = []
        for day in sorted(meals_by_day_grocery.keys()):
            diete_baml_grocery.append(DietaBAML(
                giorno=day,  # Direct BAML enum
                pasti=meals_by_day_grocery[day]
            ))

        # Generate grocery list using BAML
        try:
            grocery = await b.GeneraListaSpesa(diete_baml_grocery)
        except Exception as e:
            logger.exception("Error generating grocery list during diet modification")
            raise HTTPException(502, f"Grocery list generation failed: {e}")

        # Save grocery list
        grocery_list = self.grocery_list_repo.create_grocery_list(
            grocery_list_id=str(uuid.uuid4()),
            weekly_diet_id=saved.id
        )

        for ingr in grocery.ingredienti:
            existing_ingr = self.ingredient_repo.get_by_name(ingr.nome)

            # Create ingredient if it doesn't exist
            if not existing_ingr:
                existing_ingr = self.ingredient_repo.create_ingredient(
                    ingredient_id=str(uuid.uuid4()),
                    name=ingr.nome,
                    unit=ingr.unita,
                )

            # Create grocery list item
            self.grocery_list_item_repo.create_grocery_item(
                item_id=str(uuid.uuid4()),
                grocery_list_id=grocery_list.id,
                ingredient_id=existing_ingr.id,
                quantity=ingr.quantita,
            )

        # Commit grocery list changes
        self.db.commit()

        # Build response using BAML enums directly from saved meals
        response_meals: List[PastoSchema] = []
        for m in saved.meals:
            response_meals.append(
                PastoSchema(
                    id=m.id,
                    tipoPasto=TipoPastoSchema(
                        tipo=m.meal_type,  # Direct BAML enum
                        orario=m.time,
                        ricetta=m.recipe or "",
                    ),
                    ingredienti=m.ingredienti,  # Just pass through the string
                    calorie=m.calories,
                    day=m.day,  # Direct BAML enum
                )
            )

        # Build grocery list items directly from BAML response (not from DB reload)
        # This avoids session cache issues and matches the pattern in create_grocery_list_for_diet
        grocery_items = [
            IngredienteSchema(
                nome=ingr.nome,
                quantita=ingr.quantita,
                unita=ingr.unita
            )
            for ingr in grocery.ingredienti
        ]

        # Return diet with grocery list
        from app.schemas import DietaConLista
        return DietaConLista(
            dieta=DietaSettimanaleSchema(
                id=saved.id,
                nome=saved.name,
                dataInizio=saved.start_date.isoformat(),
                dataFine=saved.end_date.isoformat(),
                pasti=response_meals,
            ),
            listaSpesa=ListaSpesaSchema(ingredienti=grocery_items)
        )

    def delete_diet(self, diet_id: str, user_id: str) -> bool:
        """Delete a weekly diet plan"""
        from sqlalchemy import delete as sql_delete
        from app.models import WeeklyDiet

        # Use a direct delete query with user_id check for performance
        # This leverages database CASCADE deletes instead of ORM
        stmt = (
            sql_delete(WeeklyDiet)
            .where(WeeklyDiet.id == diet_id, WeeklyDiet.user_id == user_id)
        )

        result = self.db.execute(stmt)
        rows_deleted = cast(CursorResult, result).rowcount

        if rows_deleted == 0:
            # Check if diet exists at all (for better error message)
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