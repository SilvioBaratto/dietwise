"""Authentication dependencies for FastAPI using Supabase JWT validation"""

from datetime import datetime, timezone
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.exceptions import AuthenticationError
from app.database import get_db
from app.auth.supabase_auth import validate_supabase_token_sync

logger = logging.getLogger(__name__)

# HTTPBearer security scheme - adds "Authorize" button to Swagger UI
bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Enter your Supabase JWT token",
    auto_error=False  # Handle missing token manually for better error messages
)


def get_current_user_from_token(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> dict:
    """
    Dependency to get the current authenticated user from Supabase JWT.

    Uses get_claims() for fast, cached JWKS-based validation.
    Automatically creates user in local database if they don't exist yet.

    Args:
        credentials: Bearer token credentials from HTTPBearer
        db: Database session

    Returns:
        User data dictionary

    Raises:
        AuthenticationError: If token is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Validate JWT using get_claims() - fast, cached JWKS verification
    claims_data = validate_supabase_token_sync(token, require_fresh=False)

    if not claims_data:
        raise AuthenticationError("Invalid or expired token")

    user_id = claims_data.get("id")
    if not user_id:
        raise AuthenticationError("Token missing user ID")

    # Check if user is anonymous (Supabase anonymous auth)
    if claims_data.get("is_anonymous"):
        raise AuthenticationError("Anonymous users not allowed")

    # Get or create user in our database
    from app.models import User
    from sqlalchemy import select, or_

    try:
        email = claims_data.get("email")

        # Get user from our database by ID or email
        stmt = select(User).where(
            or_(User.id == user_id, User.email == email)
        )
        result = db.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            # User doesn't exist - create new user
            logger.info(f"Creating new user in database: {user_id} ({email})")

            db_user = User(
                id=user_id,
                email=email,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        elif db_user.id != user_id:
            # User exists with same email but different ID - use existing user
            logger.warning(
                f"User ID mismatch for {email}: Supabase ID={user_id}, DB ID={db_user.id}. "
                f"Using existing DB user to preserve data."
            )
            user_id = db_user.id

        # Return combined user data
        return {
            "id": str(db_user.id),
            "email": db_user.email,
            "username": db_user.email.split("@")[0] if db_user.email else None,
            "is_active": True,
            "is_approved": db_user.is_approved,
            "is_admin": db_user.is_admin,
            "created_at": db_user.created_at.isoformat(),
            "role": claims_data.get("role", "authenticated"),
            "aal": claims_data.get("aal"),
            "session_id": claims_data.get("session_id"),
            "user_metadata": claims_data.get("user_metadata", {}),
            "app_metadata": claims_data.get("app_metadata", {}),
        }

    except Exception as e:
        logger.error(f"Error fetching/creating user data: {e}")
        db.rollback()
        raise AuthenticationError(f"Failed to authenticate user: {str(e)}")


def get_current_user(
    user_data: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Dependency to require an authenticated and approved user.

    Args:
        user_data: User data from token validation

    Returns:
        User data dictionary

    Raises:
        AuthenticationError: If user is not authenticated, inactive, or not approved
    """
    if not user_data.get("is_active", True):
        raise AuthenticationError("User account is inactive")

    # Check if user is approved (admins are always approved)
    if not user_data.get("is_approved") and not user_data.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please wait for admin approval."
        )

    return user_data


def require_admin(
    user_data: dict = Depends(get_current_user_from_token),
) -> dict:
    """
    Dependency to require an admin user.

    Args:
        user_data: User data from token validation

    Returns:
        User data dictionary

    Raises:
        HTTPException: If user is not an admin
    """
    if not user_data.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user_data


def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """
    Dependency to optionally get the current user (doesn't raise if no token).

    Args:
        credentials: Bearer token credentials from HTTPBearer
        db: Database session

    Returns:
        User data if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return get_current_user_from_token(credentials, db)
    except AuthenticationError:
        return None


def require_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to explicitly require authentication (alias for get_current_user).

    Args:
        current_user: Current authenticated user

    Returns:
        User data dictionary
    """
    return current_user


def get_user_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Dependency to get the current user's ID as string.

    Args:
        current_user: Current authenticated user

    Returns:
        User ID as string
    """
    return str(current_user["id"])


# Type aliases for dependency injection
CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[Optional[dict], Depends(get_optional_user)]
AdminUser = Annotated[dict, Depends(require_admin)]
RequireAuth = Depends(require_user)
UserId = Annotated[str, Depends(get_user_id)]
