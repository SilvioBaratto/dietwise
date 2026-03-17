"""User repository for data access operations"""


from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserSettings


class UserRepository:
    """Repository for User operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create_user(self, user_id: str, email: str) -> User:
        """Create a new user"""
        user = User(id=user_id, email=email)
        self.db.add(user)
        self.db.flush()
        return user


class UserSettingsRepository:
    """Repository for UserSettings operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> UserSettings | None:
        """Get user settings by user ID"""
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create_user_settings(
        self,
        settings_id: str,
        user_id: str,
        age: int | None = None,
        sex: str | None = None,
        weight: float | None = None,
        height: float | None = None,
        other_data: str | None = None,
        goals: str | None = None
    ) -> UserSettings:
        """Create new user settings"""
        settings = UserSettings(
            id=settings_id,
            user_id=user_id,
            age=age,
            sex=sex,
            weight=weight,
            height=height,
            other_data=other_data,
            goals=goals
        )
        self.db.add(settings)
        self.db.flush()
        return settings

    def update_user_settings(
        self,
        user_id: str,
        age: int | None = None,
        sex: str | None = None,
        weight: float | None = None,
        height: float | None = None,
        other_data: str | None = None,
        goals: str | None = None
    ) -> UserSettings | None:
        """Update existing user settings"""
        settings = self.get_by_user_id(user_id)
        if not settings:
            return None

        if age is not None:
            settings.age = age
        if sex is not None:
            settings.sex = sex
        if weight is not None:
            settings.weight = weight
        if height is not None:
            settings.height = height
        if other_data is not None:
            settings.other_data = other_data
        if goals is not None:
            settings.goals = goals

        self.db.flush()
        self.db.refresh(settings)
        return settings

    def update_provider_preferences(
        self, user_id: str, provider: str, model: str
    ) -> UserSettings | None:
        """Update preferred_provider and preferred_model on existing settings."""
        settings = self.get_by_user_id(user_id)
        if not settings:
            return None
        settings.preferred_provider = provider
        settings.preferred_model = model
        self.db.flush()
        self.db.refresh(settings)
        return settings
