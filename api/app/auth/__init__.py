"""Authentication system for API Diet"""

from .supabase_auth import get_supabase_client, validate_supabase_token, initialize_supabase, close_supabase
from .dependencies import (
    bearer_scheme,
    get_current_user,
    get_current_user_from_token,
    get_optional_user,
    require_user,
    get_user_id,
    CurrentUser,
    OptionalUser,
    RequireAuth,
    UserId,
)

__all__ = [
    # Supabase integration
    "get_supabase_client",
    "validate_supabase_token",
    "initialize_supabase",
    "close_supabase",

    # Security scheme
    "bearer_scheme",

    # Authentication dependencies
    "get_current_user",
    "get_current_user_from_token",
    "get_optional_user",
    "require_user",
    "get_user_id",

    # Type aliases
    "CurrentUser",
    "OptionalUser",
    "RequireAuth",
    "UserId",
]