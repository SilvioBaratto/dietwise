"""Meal repository for data access operations"""

from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.models import Meal, MealIngredient, Ingredient, GroceryList, GroceryListItem, TipoPasto, GiornoSettimana, UnitaMisura


class MealRepository:
    """Repository for Meal operations"""

    def __init__(self, db: Session):
        self.db = db
    
    def get_with_ingredients(self, meal_id: str) -> Optional[Meal]:
        """Get meal with all ingredients and weekly diet"""
        stmt = (
            select(Meal)
            .where(Meal.id == meal_id)
            .options(
                selectinload(Meal.weekly_diet),
                selectinload(Meal.ingredients).selectinload(MealIngredient.ingredient),
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def create_meal(
        self,
        meal_id: str,
        weekly_diet_id: str,
        meal_type: TipoPasto,
        day: GiornoSettimana,
        time: str,
        recipe: str,
        ingredienti: str,
        calories: int
    ) -> Meal:
        """Create a new meal"""
        meal = Meal(
            id=meal_id,
            weekly_diet_id=weekly_diet_id,
            meal_type=meal_type,
            day=day,
            time=time,
            recipe=recipe,
            ingredienti=ingredienti,
            calories=calories,
        )
        self.db.add(meal)
        self.db.flush()
        return meal
    
    def get_meals_by_diet(self, diet_id: str) -> List[Meal]:
        """Get all meals for a specific diet"""
        stmt = (
            select(Meal)
            .where(Meal.weekly_diet_id == diet_id)
            .options(
                selectinload(Meal.ingredients).selectinload(MealIngredient.ingredient)
            )
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())


class IngredientRepository:
    """Repository for Ingredient operations"""

    def __init__(self, db: Session):
        self.db = db
    
    def get_by_name(self, name: str) -> Optional[Ingredient]:
        """Get ingredient by name"""
        stmt = select(Ingredient).where(Ingredient.name == name)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def create_ingredient(self, ingredient_id: str, name: str, unit: UnitaMisura) -> Ingredient:
        """Create a new ingredient"""
        ingredient = Ingredient(
            id=ingredient_id,
            name=name,
            unit=unit,
        )
        self.db.add(ingredient)
        self.db.flush()
        return ingredient


class MealIngredientRepository:
    """Repository for MealIngredient operations"""

    def __init__(self, db: Session):
        self.db = db
    
    def create_meal_ingredient(
        self,
        meal_ingredient_id: str,
        meal_id: str,
        ingredient_id: str,
        quantity: float
    ) -> MealIngredient:
        """Create a new meal ingredient relationship"""
        meal_ingredient = MealIngredient(
            id=meal_ingredient_id,
            meal_id=meal_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        )
        self.db.add(meal_ingredient)
        self.db.flush()
        return meal_ingredient


class GroceryListRepository:
    """Repository for GroceryList operations"""

    def __init__(self, db: Session):
        self.db = db
    
    def create_grocery_list(self, grocery_list_id: str, weekly_diet_id: str) -> GroceryList:
        """Create a new grocery list"""
        grocery_list = GroceryList(
            id=grocery_list_id,
            weekly_diet_id=weekly_diet_id
        )
        self.db.add(grocery_list)
        self.db.flush()
        return grocery_list


class GroceryListItemRepository:
    """Repository for GroceryListItem operations"""

    def __init__(self, db: Session):
        self.db = db
    
    def create_grocery_item(
        self,
        item_id: str,
        grocery_list_id: str,
        ingredient_id: str,
        quantity: float
    ) -> GroceryListItem:
        """Create a new grocery list item"""
        item = GroceryListItem(
            id=item_id,
            grocery_list_id=grocery_list_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        )
        self.db.add(item)
        self.db.flush()
        return item