"""ApiKeyService — orchestrates encrypt/validate/store lifecycle for BYOK keys."""

from datetime import UTC, datetime
import logging

from sqlalchemy.orm import Session

from app.exceptions import (
    ApiKeyNotConfiguredError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.user_repository import UserSettingsRepository
from app.schemas.api_key import (
    ApiKeyResponseSchema,
    ProviderInfo,
    ProviderPreferencesResponse,
    ProvidersResponse,
)
from app.services.api_key_validation_service import ApiKeyValidationService
from app.services.encryption_service import encryption_service
from app.utils.llm_providers import PROVIDERS, get_provider_spec

logger = logging.getLogger(__name__)


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
        self,
        user_id: str,
        provider: str,
        api_key: str | None,
        base_url: str | None = None,
        api_version: str | None = None,
        ip: str = "unknown",
    ) -> ApiKeyResponseSchema:
        """Validate, encrypt, and persist a user API key. Returns hint only."""
        spec = get_provider_spec(provider)
        if spec.requires_api_key and not api_key:
            raise ValidationError(f"{spec.label} requires an API key")

        is_valid, error_msg = await self.validator.validate(
            provider, api_key, base_url=base_url, api_version=api_version
        )
        if not is_valid:
            raise ValidationError(f"API key validation failed: {error_msg}")

        # Ollama-style optional key: encrypt a sentinel empty string so the
        # NOT NULL encrypted_key/encryption_nonce columns stay unchanged.
        plaintext_key = api_key or ""
        ciphertext, nonce = self.encryption.encrypt(plaintext_key)
        key_hint = "..." + plaintext_key[-4:] if plaintext_key else "(none)"
        api_key = ""  # best-effort plaintext clear

        record = self.repo.create(
            user_id=user_id,
            provider=provider,
            encrypted_key=ciphertext,
            encryption_nonce=nonce,
            key_hint=key_hint,
            base_url=base_url,
            api_version=api_version,
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
        return self.encryption.decrypt(record.encrypted_key, record.encryption_nonce)

    def update_preferences(self, user_id: str, provider: str, model: str) -> None:
        """Persist the user's preferred LLM provider and model."""
        spec = get_provider_spec(provider)
        if not spec.free_form_models and model not in spec.curated_models:
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
    def get_providers_info() -> ProvidersResponse:
        """Return metadata for every supported LLM provider."""
        return ProvidersResponse(
            providers=[
                ProviderInfo(
                    slug=spec.slug,
                    label=spec.label,
                    requires_api_key=spec.requires_api_key,
                    requires_base_url=spec.requires_base_url,
                    requires_api_version=spec.requires_api_version,
                    default_base_url=spec.default_base_url,
                    free_form_models=spec.free_form_models,
                    models=list(spec.curated_models),
                    default_model=spec.default_model,
                    key_format_hint=spec.key_format_hint,
                )
                for spec in PROVIDERS.values()
            ]
        )
