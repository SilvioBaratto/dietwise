"""Diet repository for data access operations"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import GroceryList, GroceryListItem, Meal, MealIngredient, WeeklyDiet
from app.repositories.base_repository import BaseRepository
from app.schemas import DietSummary


class DietRepository(BaseRepository[WeeklyDiet, DietSummary, DietSummary]):
    """Repository for WeeklyDiet operations"""

    def __init__(self, db: Session):
        super().__init__(WeeklyDiet, db)

    def get_user_diets(self, user_id: str) -> list[WeeklyDiet]:
        """Get all diets for a specific user"""
        stmt = (
            select(WeeklyDiet)
            .where(WeeklyDiet.user_id == user_id)
            .order_by(WeeklyDiet.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_with_meals(self, diet_id: str, user_id: str) -> WeeklyDiet | None:
        """Get diet with all meals and ingredients"""
        stmt = (
            select(WeeklyDiet)
            .where(WeeklyDiet.id == diet_id, WeeklyDiet.user_id == user_id)
            .options(
                selectinload(WeeklyDiet.meals)
                .selectinload(Meal.ingredients)
                .selectinload(MealIngredient.ingredient)
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_current_week_diet(self, user_id: str, today: date | None = None) -> WeeklyDiet | None:
        """Get diet for current week with all related data"""
        if today is None:
            today = date.today()

        stmt = (
            select(WeeklyDiet)
            .where(
                WeeklyDiet.user_id == user_id,
                WeeklyDiet.start_date <= today,
                WeeklyDiet.end_date >= today,
            )
            .options(
                selectinload(WeeklyDiet.meals)
                .selectinload(Meal.ingredients)
                .selectinload(MealIngredient.ingredient),
                selectinload(WeeklyDiet.grocery_list)
                .selectinload(GroceryList.items)
                .selectinload(GroceryListItem.ingredient),
            )
            .order_by(WeeklyDiet.created_at.desc())
            .limit(1)
        )
        result = self.db.execute(stmt)
        return result.scalars().first()

    def create_diet(
        self,
        user_id: str,
        diet_id: str,
        start_date: date,
        end_date: date,
        name: str
    ) -> WeeklyDiet:
        """Create a new weekly diet"""
        weekly = WeeklyDiet(
            id=diet_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            name=name,
        )
        self.db.add(weekly)
        self.db.flush()
        return weekly

    def get_with_grocery_list(self, diet_id: str, user_id: str) -> WeeklyDiet | None:
        """Get diet with grocery list and ingredients"""
        stmt = (
            select(WeeklyDiet)
            .where(WeeklyDiet.id == diet_id, WeeklyDiet.user_id == user_id)
            .options(
                selectinload(WeeklyDiet.grocery_list)
                .selectinload(GroceryList.items)
                .selectinload(GroceryListItem.ingredient)
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
