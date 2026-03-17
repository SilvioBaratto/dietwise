"""Supabase authentication integration with JWT validation"""

from dataclasses import dataclass
import logging
import time
from typing import Any

from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class JwtClaims:
    """Supabase JWT claims structure"""

    iss: str  # Issuer
    sub: str  # Subject (user ID)
    aud: str  # Audience
    exp: int  # Expiration time
    iat: int  # Issued at
    role: str  # Postgres role (authenticated, anon, etc.)
    email: str | None = None
    phone: str | None = None
    aal: str | None = None  # Authentication Assurance Level
    session_id: str | None = None
    is_anonymous: bool | None = None
    app_metadata: dict[str, Any] | None = None
    user_metadata: dict[str, Any] | None = None


class SupabaseAuthManager:
    """
    Supabase authentication manager using get_claims() for fast JWT validation.

    Uses JWKS-based verification (cached) for performance.
    Falls back to get_user() when full user data is needed.
    """

    def __init__(self):
        self._client: Client | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Supabase client"""
        if self._initialized:
            return

        logger.info("Initializing Supabase authentication client...")

        try:
            if not settings.supabase_url:
                raise ValueError("SUPABASE_URL is required")
            if not settings.supabase_key:
                raise ValueError("SUPABASE_KEY is required")

            logger.info(f"Connecting to Supabase: {settings.supabase_url}")

            client_options = SyncClientOptions(
                persist_session=False,
                auto_refresh_token=False,
                headers={
                    "User-Agent": "API-Diet/1.0.0",
                    "X-Client-Info": "fastapi-backend",
                },
            )

            self._client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_key,
                options=client_options,
            )

            self._initialized = True
            logger.info("Supabase authentication client initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize Supabase client: {e}"
            logger.error(error_msg)
            if settings.is_development:
                logger.warning(
                    "Supabase initialization failed but continuing in development mode"
                )
                self._initialized = False
            else:
                raise RuntimeError(error_msg) from e

    def get_client(self) -> Client:
        """Get the configured Supabase client"""
        if not self._initialized or not self._client:
            raise RuntimeError(
                "Supabase client not initialized. Call initialize() first."
            )
        return self._client

    async def validate_jwt_claims(self, token: str) -> dict[str, Any] | None:
        """
        Validate JWT using get_claims() - fast, cached JWKS verification.

        This method:
        1. Verifies JWT signature against Supabase's JWKS endpoint (cached)
        2. Validates expiration and other standard claims
        3. Returns decoded claims without a server round-trip

        Args:
            token: JWT access token string

        Returns:
            Dict with claims if valid, None if invalid
        """
        try:
            if not self._initialized:
                await self.initialize()

            client = self.get_client()

            # Use get_claims() for fast, cached JWKS-based verification
            # This is preferred over get_user() for performance
            # Note: ClaimsResponse is a TypedDict, use dictionary-style access
            response = client.auth.get_claims(jwt=token)

            if response and response.get("claims"):
                claims = response["claims"]

                # Validate expiration
                exp = claims.get("exp")
                if not exp or exp < time.time():
                    logger.warning("Token expired")
                    return None

                # Validate issuer matches our Supabase project
                iss = claims.get("iss")
                expected_issuer = f"{settings.supabase_url}/auth/v1"
                if iss != expected_issuer:
                    logger.warning(
                        f"Invalid issuer: {iss}, expected: {expected_issuer}"
                    )
                    return None

                # Validate audience
                aud = claims.get("aud")
                if aud != "authenticated":
                    logger.warning(f"Invalid audience: {aud}")
                    return None

                # Validate role is authenticated (not anon)
                role = claims.get("role")
                if role not in ("authenticated", "service_role"):
                    logger.warning(f"Invalid role: {role}")
                    return None

                return {
                    "id": claims.get("sub"),
                    "email": claims.get("email"),
                    "role": role,
                    "aal": claims.get("aal"),
                    "session_id": claims.get("session_id"),
                    "is_anonymous": claims.get("is_anonymous"),
                    "exp": exp,
                    "iat": claims.get("iat"),
                    "iss": iss,
                    "aud": aud,
                    "app_metadata": claims.get("app_metadata") or {},
                    "user_metadata": claims.get("user_metadata") or {},
                }

        except Exception as e:
            logger.warning(f"JWT claims validation failed: {e}")

        return None

    async def get_user_from_token(self, token: str) -> dict[str, Any] | None:
        """
        Get full user data from Supabase Auth server.

        This method calls the Auth server directly to:
        1. Verify the token is still valid (not revoked)
        2. Get the latest user data

        Use this when you need to ensure the session hasn't been logged out,
        or when you need fresh user metadata.

        Args:
            token: JWT access token string

        Returns:
            Dict with user data if valid, None if invalid
        """
        try:
            if not self._initialized:
                await self.initialize()

            client = self.get_client()
            response = client.auth.get_user(jwt=token)

            if response and response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at,
                    "updated_at": response.user.updated_at,
                    "user_metadata": response.user.user_metadata or {},
                    "app_metadata": response.user.app_metadata or {},
                }

        except Exception as e:
            logger.warning(f"Get user failed: {e}")

        return None

    async def validate_token(
        self, token: str, require_fresh: bool = False
    ) -> dict[str, Any] | None:
        """
        Validate a Supabase JWT token.

        Args:
            token: JWT access token string
            require_fresh: If True, always call get_user() for fresh data.
                          If False, use get_claims() for fast validation.

        Returns:
            User/claims data if valid, None if invalid
        """
        if require_fresh:
            # Full server validation - slower but checks session isn't revoked
            return await self.get_user_from_token(token)
        else:
            # Fast JWKS-based validation - preferred for API calls
            return await self.validate_jwt_claims(token)

    def get_config_info(self) -> dict[str, Any]:
        """Get configuration information for debugging"""
        return {
            "url_configured": bool(settings.supabase_url),
            "key_configured": bool(settings.supabase_key),
            "client_initialized": self._initialized,
            "environment": settings.environment,
            "jwks_endpoint": f"{settings.supabase_url}/auth/v1/.well-known/jwks.json",
        }


# Global instance
_supabase_auth_manager: SupabaseAuthManager | None = None


async def get_supabase_auth_manager() -> SupabaseAuthManager:
    """Get the global Supabase auth manager instance"""
    global _supabase_auth_manager

    if _supabase_auth_manager is None:
        _supabase_auth_manager = SupabaseAuthManager()
        await _supabase_auth_manager.initialize()

    return _supabase_auth_manager


async def get_supabase_client() -> Client:
    """Get the Supabase client instance"""
    manager = await get_supabase_auth_manager()
    return manager.get_client()


async def validate_supabase_token(
    token: str, require_fresh: bool = False
) -> dict[str, Any] | None:
    """
    Validate a Supabase JWT token.

    Args:
        token: JWT access token string
        require_fresh: If True, validates with Auth server (slower, checks revocation).
                      If False, uses cached JWKS validation (faster).

    Returns:
        User/claims data if valid, None if invalid
    """
    manager = await get_supabase_auth_manager()
    return await manager.validate_token(token, require_fresh=require_fresh)


def get_supabase_auth_manager_sync() -> SupabaseAuthManager:
    """Get the global Supabase auth manager instance (synchronous)"""
    global _supabase_auth_manager

    if _supabase_auth_manager is None:
        import asyncio

        _supabase_auth_manager = SupabaseAuthManager()
        asyncio.run(_supabase_auth_manager.initialize())

    return _supabase_auth_manager


def validate_supabase_token_sync(
    token: str, require_fresh: bool = False
) -> dict[str, Any] | None:
    """
    Validate a Supabase JWT token (synchronous version).

    Args:
        token: JWT access token string
        require_fresh: If True, validates with Auth server.
                      If False, uses cached JWKS validation.

    Returns:
        User/claims data if valid, None if invalid
    """
    manager = get_supabase_auth_manager_sync()
    import asyncio

    return asyncio.run(manager.validate_token(token, require_fresh=require_fresh))


async def get_supabase_config_info() -> dict[str, Any]:
    """Get Supabase configuration information for health checks"""
    if _supabase_auth_manager is None:
        return {
            "url_configured": bool(settings.supabase_url),
            "key_configured": bool(settings.supabase_key),
            "client_initialized": False,
            "environment": settings.environment,
        }
    return _supabase_auth_manager.get_config_info()


async def initialize_supabase():
    """Initialize Supabase auth manager - called during startup"""
    await get_supabase_auth_manager()


async def close_supabase():
    """Close Supabase connections - called during shutdown"""
    pass
