"""User service for business logic operations"""

import uuid
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.repositories import UserRepository, UserSettingsRepository
from app.schemas import UserSettingsIn, UserSettingsOut

logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related business logic"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.user_settings_repo = UserSettingsRepository(db)

    def get_user_settings(self, user_id: str) -> UserSettingsOut:
        """Get user settings"""
        settings = self.user_settings_repo.get_by_user_id(user_id)

        if settings is None:
            raise HTTPException(
                status_code=404, detail="No settings found for this user."
            )

        return UserSettingsOut(
            id=settings.id,
            user_id=settings.user_id,
            age=settings.age,
            sex=settings.sex,
            weight=settings.weight,
            height=settings.height,
            other_data=settings.other_data,
            goals=settings.goals,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )

    def update_user_settings(
        self, user_id: str, payload: UserSettingsIn
    ) -> UserSettingsOut:
        """Create or update user settings"""
        settings = self.user_settings_repo.get_by_user_id(user_id)

        if settings is None:
            # Create new settings
            settings = self.user_settings_repo.create_user_settings(
                settings_id=str(uuid.uuid4()),
                user_id=user_id,
                age=payload.age,
                sex=payload.sex,
                weight=payload.weight,
                height=payload.height,
                other_data=payload.other_data,
                goals=payload.goals,
            )
        else:
            # Update existing settings
            update_data = payload.model_dump(exclude_unset=True)
            settings = self.user_settings_repo.update_user_settings(
                user_id=user_id, **update_data
            )

            if settings is None:
                raise HTTPException(
                    status_code=404,
                    detail="User settings not found for update"
                )

        self.db.commit()
        self.db.refresh(settings)

        return UserSettingsOut(
            id=settings.id,
            user_id=settings.user_id,
            age=settings.age,
            sex=settings.sex,
            weight=settings.weight,
            height=settings.height,
            other_data=settings.other_data,
            goals=settings.goals,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )
