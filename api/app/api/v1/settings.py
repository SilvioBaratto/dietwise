"""User settings API endpoints"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.services import UserService
from app.schemas import UserSettingsIn, UserSettingsOut

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "/get_user_settings",
    response_model=UserSettingsOut,
    status_code=status.HTTP_200_OK,
)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve the current user's settings (404 if none exist)"""
    user_id = current_user["id"]
    user_service = UserService(db)
    return user_service.get_user_settings(user_id)


@router.post(
    "/update_user_settings",
    response_model=UserSettingsOut,
    status_code=status.HTTP_200_OK,
)
def update_user_settings(
    payload: UserSettingsIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create or update the current user's settings"""
    user_id = current_user["id"]
    user_service = UserService(db)
    return user_service.update_user_settings(user_id, payload)