"""BYOK API key management endpoints."""

import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.dependencies import RateLimiter
from app.schemas.api_key import (
    ApiKeyResponseSchema,
    ApiKeySaveRequest,
    AvailableModelsResponse,
    ProviderPreferencesRequest,
    ProviderPreferencesResponse,
    ValidateKeyRequest,
    ValidateKeyResponse,
)
from app.services.api_key_service import ApiKeyService
from app.services.api_key_validation_service import ApiKeyValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

rate_limit_keys = RateLimiter(requests=10, window=60, per_user=True)
rate_limit_validate = RateLimiter(requests=20, window=60, per_user=True)


def _get_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _set_no_cache(response: Response) -> None:
    """Set cache-control headers to prevent browser caching of key data."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post(
    "",
    response_model=ApiKeyResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Save or update an API key for a provider",
)
async def save_api_key(
    request: ApiKeySaveRequest,
    http_request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate, encrypt, and persist a user-supplied LLM API key."""
    _set_no_cache(response)
    rate_limit_keys(http_request, current_user)
    service = ApiKeyService(db)
    return await service.save_key(
        current_user["id"], request.provider, request.api_key,
        ip=_get_ip(http_request),
    )


@router.get(
    "",
    response_model=list[ApiKeyResponseSchema],
    status_code=status.HTTP_200_OK,
    summary="List stored API keys (key hints only)",
)
def list_api_keys(
    http_request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all stored key records. Full keys are never included."""
    _set_no_cache(response)
    rate_limit_keys(http_request, current_user)
    service = ApiKeyService(db)
    return service.get_user_keys(current_user["id"])


@router.delete(
    "/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a stored API key for a provider",
)
def delete_api_key(
    http_request: Request,
    response: Response,
    provider: Literal["openai", "anthropic", "google"] = Path(
        ..., description="Provider name: openai | anthropic | google"
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove the stored API key for the given provider."""
    _set_no_cache(response)
    rate_limit_keys(http_request, current_user)
    service = ApiKeyService(db)
    deleted = service.delete_key(
        current_user["id"], provider, ip=_get_ip(http_request)
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No API key stored for provider '{provider}'",
        )
    return None


@router.post(
    "/validate",
    response_model=ValidateKeyResponse,
    status_code=status.HTTP_200_OK,
    summary="Test an API key without saving it",
)
async def validate_api_key(
    request: ValidateKeyRequest,
    http_request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """Validate a key against the provider's API without storing it."""
    _set_no_cache(response)
    rate_limit_validate(http_request, current_user)
    validator = ApiKeyValidationService()
    is_valid, error_msg = await validator.validate(
        request.provider, request.api_key
    )
    logger.info(
        "api_key_event",
        extra={
            "event": "api_key_validated",
            "user_id": current_user["id"],
            "provider": request.provider,
            "key_hint": "..." + request.api_key[-4:],
            "ip": _get_ip(http_request),
            "is_valid": is_valid,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
    return ValidateKeyResponse(
        provider=request.provider,
        is_valid=is_valid,
        error=error_msg if not is_valid else None,
    )


@router.put(
    "/preferences",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Set preferred LLM provider and model",
)
def set_preferences(
    request: ProviderPreferencesRequest,
    http_request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persist the user's preferred LLM provider and model."""
    _set_no_cache(response)
    rate_limit_keys(http_request, current_user)
    service = ApiKeyService(db)
    service.update_preferences(
        current_user["id"], request.provider, request.model
    )
    return None


@router.get(
    "/preferences",
    response_model=ProviderPreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current preferred LLM provider and model",
)
def get_preferences(
    http_request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the user's currently preferred provider and model."""
    _set_no_cache(response)
    rate_limit_keys(http_request, current_user)
    service = ApiKeyService(db)
    return service.get_preferences(current_user["id"])


@router.get(
    "/available-models",
    response_model=AvailableModelsResponse,
    status_code=status.HTTP_200_OK,
    summary="List supported models per provider",
)
def get_available_models(
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """Return the static list of supported LLM models grouped by provider."""
    _set_no_cache(response)
    return ApiKeyService.get_available_models()
