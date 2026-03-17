"""Diet-related database models"""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from baml_client.types import GiornoSettimana, TipoPasto, UnitaMisura


class User(Base):
    """User model"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Access control
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default='false',
        nullable=False,
        comment="True if user has been approved by admin"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default='false',
        nullable=False,
        comment="True if user is an admin"
    )

    # Table constraints
    __table_args__ = (
        Index('idx_users_email', 'email'),  # Explicit index for email lookups
        Index('idx_users_approval_status', 'is_approved'),  # For filtering pending users
    )

    # Relationships
    diets = relationship("WeeklyDiet", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("UserApiKey", back_populates="user", cascade="all, delete-orphan")


class WeeklyDiet(Base):
    """Weekly diet plan model"""
    __tablename__ = "weekly_diets"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint('start_date < end_date', name='chk_weekly_diets_date_range'),
        Index('idx_weekly_diets_user_id', 'user_id'),
        Index('idx_weekly_diets_dates', 'user_id', 'start_date', 'end_date'),
        Index('idx_weekly_diets_user_created', 'user_id', 'created_at'),
    )

    # Relationships
    user = relationship("User", back_populates="diets")
    meals = relationship("Meal", back_populates="weekly_diet", cascade="all, delete-orphan")
    grocery_list = relationship("GroceryList", back_populates="weekly_diet", uselist=False, cascade="all, delete-orphan")


class Meal(Base):
    """Individual meal model"""
    __tablename__ = "meals"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    weekly_diet_id: Mapped[str] = mapped_column(String, ForeignKey("weekly_diets.id", ondelete="CASCADE"), nullable=False)
    meal_type: Mapped[TipoPasto] = mapped_column(SQLEnum(TipoPasto), nullable=False)
    day: Mapped[GiornoSettimana] = mapped_column(SQLEnum(GiornoSettimana), nullable=False)
    time: Mapped[str] = mapped_column(String, nullable=True)
    recipe: Mapped[str] = mapped_column(String, nullable=True)
    ingredienti: Mapped[str] = mapped_column(String, nullable=False, default="")  # Comma-separated ingredient string
    calories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proteine: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    carboidrati: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grassi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Table constraints
    __table_args__ = (
        CheckConstraint('calories >= 0', name='chk_meals_positive_calories'),
        CheckConstraint('proteine >= 0', name='chk_meals_positive_proteine'),
        CheckConstraint('carboidrati >= 0', name='chk_meals_positive_carboidrati'),
        CheckConstraint('grassi >= 0', name='chk_meals_positive_grassi'),
        Index('idx_meals_weekly_diet_id', 'weekly_diet_id'),
        Index('idx_meals_weekly_diet_day', 'weekly_diet_id', 'day'),
        Index('idx_meals_weekly_diet_type', 'weekly_diet_id', 'meal_type'),
    )

    # Relationships
    weekly_diet = relationship("WeeklyDiet", back_populates="meals")
    ingredients = relationship("MealIngredient", back_populates="meal", cascade="all, delete-orphan")


class Ingredient(Base):
    """Ingredient model"""
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    unit: Mapped[UnitaMisura] = mapped_column(SQLEnum(UnitaMisura), nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint("name != ''", name='chk_ingredients_non_empty_name'),
        Index('idx_ingredients_name', 'name'),  # For ingredient lookups by name
    )

    # Relationships
    meals = relationship("MealIngredient", back_populates="ingredient", cascade="all, delete-orphan")
    grocery_items = relationship("GroceryListItem", back_populates="ingredient", cascade="all, delete-orphan")


class MealIngredient(Base):
    """Many-to-many relationship between meals and ingredients"""
    __tablename__ = "meal_ingredients"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    meal_id: Mapped[str] = mapped_column(String, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(String, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='chk_meal_ingredients_positive_quantity'),
        Index('idx_meal_ingredients_meal_id', 'meal_id'),
        Index('idx_meal_ingredients_ingredient_id', 'ingredient_id'),
        Index('idx_meal_ingredients_meal_ingredient', 'meal_id', 'ingredient_id'),
    )

    # Relationships
    meal = relationship("Meal", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="meals")


class GroceryList(Base):
    """Grocery list model"""
    __tablename__ = "grocery_lists"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    weekly_diet_id: Mapped[str] = mapped_column(String, ForeignKey("weekly_diets.id", ondelete="CASCADE"), nullable=False)

    # Table constraints
    __table_args__ = (
        Index('idx_grocery_lists_weekly_diet_id', 'weekly_diet_id'),
    )

    # Relationships
    weekly_diet = relationship("WeeklyDiet", back_populates="grocery_list")
    items = relationship("GroceryListItem", back_populates="grocery_list", cascade="all, delete-orphan")


class GroceryListItem(Base):
    """Individual grocery list item model"""
    __tablename__ = "grocery_list_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    grocery_list_id: Mapped[str] = mapped_column(String, ForeignKey("grocery_lists.id", ondelete="CASCADE"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(String, ForeignKey("ingredients.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='chk_grocery_list_items_positive_quantity'),
        Index('idx_grocery_list_items_grocery_list_id', 'grocery_list_id'),
        Index('idx_grocery_list_items_ingredient_id', 'ingredient_id'),
        Index('idx_grocery_list_items_grocery_ingredient', 'grocery_list_id', 'ingredient_id'),
    )

    # Relationships
    grocery_list = relationship("GroceryList", back_populates="items")
    ingredient = relationship("Ingredient", back_populates="grocery_items")


class SavedRecipe(Base):
    """Saved recipe model - stores AI-generated recipes that users want to keep"""
    __tablename__ = "saved_recipes"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipe_name: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "Porridge di avena con banana"
    recipe_instructions: Mapped[str] = mapped_column(String, nullable=False)  # Generated instructions
    meal_type: Mapped[TipoPasto] = mapped_column(SQLEnum(TipoPasto), nullable=False)
    calories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint('calories >= 0', name='chk_saved_recipes_positive_calories'),
        Index('idx_saved_recipes_user_id', 'user_id'),
        Index('idx_saved_recipes_recipe_name', 'recipe_name'),
        Index('idx_saved_recipes_user_recipe', 'user_id', 'recipe_name'),
    )

    # Relationships
    user = relationship("User", backref="saved_recipes")


class UserSettings(Base):
    """User settings model"""
    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    sex: Mapped[str] = mapped_column(String(1), nullable=True)  # 'M' or 'F'
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    height: Mapped[float] = mapped_column(Float, nullable=True)
    other_data: Mapped[str] = mapped_column(String, nullable=True)
    goals: Mapped[str] = mapped_column(String, nullable=True)
    preferred_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint('age IS NULL OR (age > 0 AND age < 150)', name='chk_user_settings_valid_age'),
        CheckConstraint('weight IS NULL OR weight > 0', name='chk_user_settings_positive_weight'),
        CheckConstraint('height IS NULL OR height > 0', name='chk_user_settings_positive_height'),
        CheckConstraint(
            "preferred_provider IS NULL OR preferred_provider IN ('openai', 'google', 'anthropic')",
            name='chk_user_settings_valid_preferred_provider',
        ),
        Index('idx_user_settings_user_id', 'user_id'),
    )

    # Relationships
    user = relationship("User", back_populates="settings")
