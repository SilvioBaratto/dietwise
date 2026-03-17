"""ApiKeyService — orchestrates encrypt/validate/store lifecycle for BYOK keys."""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.exceptions import ApiKeyNotConfiguredError, ConflictError, NotFoundError, ValidationError

from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.user_repository import UserSettingsRepository
from app.schemas.api_key import (
    ApiKeyResponseSchema,
    AvailableModelsResponse,
    ProviderPreferencesResponse,
)
from app.services.api_key_validation_service import ApiKeyValidationService
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)

_AVAILABLE_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-5.4",
        "gpt-5-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
    ],
    "anthropic": [
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
    ],
    "google": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ],
}


class ApiKeyService:
    """Orchestrates the full lifecycle of user-supplied LLM API keys."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ApiKeyRepository(db)
        self.settings_repo = UserSettingsRepository(db)
        self.encryption = encryption_service
        self.validator = ApiKeyValidationService()

    def _audit(
        self, event: str, user_id: str, provider: str, key_hint: str, ip: str
    ) -> None:
        """Emit a structured audit log entry. Never receives raw API keys."""
        logger.info(
            "api_key_event",
            extra={
                "event": event,
                "user_id": user_id,
                "provider": provider,
                "key_hint": key_hint,
                "ip": ip,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    async def save_key(
        self, user_id: str, provider: str, api_key: str, ip: str = "unknown"
    ) -> ApiKeyResponseSchema:
        """Validate, encrypt, and persist a user API key. Returns hint only."""
        is_valid, error_msg = await self.validator.validate(provider, api_key)
        if not is_valid:
            raise ValidationError(f"API key validation failed: {error_msg}")

        ciphertext, nonce = self.encryption.encrypt(api_key)
        key_hint = "..." + api_key[-4:]
        api_key = ""  # best-effort plaintext clear

        record = self.repo.create(
            user_id=user_id,
            provider=provider,
            encrypted_key=ciphertext,
            encryption_nonce=nonce,
            key_hint=key_hint,
        )
        self.db.commit()
        self._audit("api_key_saved", user_id, provider, record.key_hint, ip)
        return ApiKeyResponseSchema.model_validate(record)

    def get_user_keys(self, user_id: str) -> list[ApiKeyResponseSchema]:
        """Return all stored key hints for a user. Full keys are never included."""
        records = self.repo.get_all_by_user(user_id)
        return [ApiKeyResponseSchema.model_validate(r) for r in records]

    def delete_key(self, user_id: str, provider: str, ip: str = "unknown") -> bool:
        """Delete a stored key. Returns False if the key did not exist."""
        deleted = self.repo.delete_by_user_and_provider(user_id, provider)
        if deleted:
            self.db.commit()
            self._audit("api_key_deleted", user_id, provider, "n/a", ip)
        return deleted

    def get_decrypted_key(
        self, user_id: str, provider: str, ip: str = "unknown"
    ) -> str:
        """Decrypt and return plaintext key for internal LLM dispatch.

        Never expose via API.
        """
        record = self.repo.get_by_user_and_provider(user_id, provider)
        if not record:
            raise ApiKeyNotConfiguredError(provider)
        if not record.is_valid:
            raise ConflictError(f"Stored key for '{provider}' is marked invalid")
        self._audit("api_key_decrypted", user_id, provider, record.key_hint, ip)
        return self.encryption.decrypt(
            record.encrypted_key, record.encryption_nonce
        )

    def update_preferences(
        self, user_id: str, provider: str, model: str
    ) -> None:
        """Persist the user's preferred LLM provider and model."""
        if model not in _AVAILABLE_MODELS.get(provider, []):
            raise ValidationError(
                f"Model '{model}' is not available for provider '{provider}'"
            )
        settings = self.settings_repo.update_provider_preferences(
            user_id=user_id, provider=provider, model=model
        )
        if settings is None:
            raise NotFoundError("User settings")
        self.db.commit()

    def get_preferences(self, user_id: str) -> ProviderPreferencesResponse:
        """Return the user's current preferred provider and model."""
        settings = self.settings_repo.get_by_user_id(user_id)
        if settings is None:
            return ProviderPreferencesResponse(provider=None, model=None)
        return ProviderPreferencesResponse(
            provider=settings.preferred_provider,
            model=settings.preferred_model,
        )

    @staticmethod
    def get_available_models() -> AvailableModelsResponse:
        """Return the static list of supported models per provider."""
        return AvailableModelsResponse(**_AVAILABLE_MODELS)
