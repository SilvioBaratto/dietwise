"""User repository for data access operations"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User, UserSettings


class UserRepository:
    """Repository for User operations"""

    def __init__(self, db: Session):
        self.db = db
    
    def get_by_email(self, email: str) -> Optional[User]:
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
    
    def get_by_user_id(self, user_id: str) -> Optional[UserSettings]:
        """Get user settings by user ID"""
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def create_user_settings(
        self,
        settings_id: str,
        user_id: str,
        age: Optional[int] = None,
        sex: Optional[str] = None,
        weight: Optional[float] = None,
        height: Optional[float] = None,
        other_data: Optional[str] = None,
        goals: Optional[str] = None
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
        age: Optional[int] = None,
        sex: Optional[str] = None,
        weight: Optional[float] = None,
        height: Optional[float] = None,
        other_data: Optional[str] = None,
        goals: Optional[str] = None
    ) -> Optional[UserSettings]:
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