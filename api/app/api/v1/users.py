"""Current-user API endpoints (auth-adjacent, not settings)"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_from_token
from app.database import get_db
from app.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/accept-terms",
    status_code=status.HTTP_200_OK,
)
def accept_terms(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Record that the current user has accepted the Terms & Conditions.

    Depends on get_current_user_from_token (not get_current_user) so this
    endpoint is reachable even before terms are accepted - that's the whole
    point of it existing.
    """
    user_id = current_user["id"]
    user_service = UserService(db)
    terms_accepted_at = user_service.accept_terms(user_id)
    return {"terms_accepted_at": terms_accepted_at}
