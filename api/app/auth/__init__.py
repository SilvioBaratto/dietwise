"""Authentication system for API Diet"""

from .dependencies import (
    CurrentUser,
    OptionalUser,
    RequireAuth,
    UserId,
    bearer_scheme,
    get_current_user,
    get_current_user_from_token,
    get_optional_user,
    get_user_id,
    require_user,
)
from .supabase_auth import (
    close_supabase,
    get_supabase_client,
    initialize_supabase,
    validate_supabase_token,
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
