"""Shared BAML client builder and error classifier for BYOK services."""

import logging
from typing import NoReturn

import baml_py
from sqlalchemy.orm import Session

from app.exceptions import ApiKeyNotConfiguredError, LLMProviderError, RateLimitError
from app.repositories import ApiKeyRepository, UserSettingsRepository
from app.services.encryption_service import encryption_service
from baml_client.async_client import BamlAsyncClient, b

logger = logging.getLogger(__name__)

DEFAULT_MODEL: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-haiku-20240307",
    "google": "gemini-1.5-flash",
}

PROVIDER_BAML_NAME: dict[str, str] = {
    "openai": "openai",
    "google": "google-ai",
    "anthropic": "anthropic",
}


class BamlClientFactory:
    """Builds per-user scoped BAML clients and classifies provider errors."""

    def __init__(self, db: Session, user_id: str) -> None:
        self.db = db
        self.user_id = user_id
        self.user_settings_repo = UserSettingsRepository(db)
        self.api_key_repo = ApiKeyRepository(db)
        self.provider: str = "unknown"
        self._client: BamlAsyncClient | None = None

    def get_client(self) -> BamlAsyncClient:
        """Lazy accessor — only builds the BAML client on first LLM call."""
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> BamlAsyncClient:
        """Build a per-user scoped BAML client using the user's stored API key."""
        settings = self.user_settings_repo.get_by_user_id(self.user_id)
        if not settings or not settings.preferred_provider:
            raise ApiKeyNotConfiguredError("(not configured)")

        provider = settings.preferred_provider
        model = settings.preferred_model or DEFAULT_MODEL.get(provider, "")
        self.provider = provider

        record = self.api_key_repo.get_by_user_and_provider(self.user_id, provider)
        if not record:
            raise ApiKeyNotConfiguredError(provider)
        if not record.is_valid:
            raise ApiKeyNotConfiguredError(provider)

        decrypted_key = encryption_service.decrypt(
            record.encrypted_key, record.encryption_nonce
        )
        logger.info(
            "api_key_event",
            extra={
                "event": "api_key_decrypted_for_llm",
                "user_id": self.user_id,
                "provider": provider,
                "key_hint": record.key_hint,
            },
        )

        cr = baml_py.ClientRegistry()
        baml_provider = PROVIDER_BAML_NAME.get(provider, provider)
        cr.add_llm_client(
            "UserClient", baml_provider, {"model": model, "api_key": decrypted_key}
        )
        cr.set_primary("UserClient")
        return b.with_options(client_registry=cr)

    def handle_baml_error(self, exc: Exception) -> NoReturn:
        """Classify a BAML/provider exception, invalidate key if auth error, and raise."""
        provider = self.provider
        error_str = str(exc).lower()

        if any(
            s in error_str
            for s in ("401", "unauthorized", "invalid api key", "authentication")
        ):
            record = self.api_key_repo.get_by_user_and_provider(
                self.user_id, provider
            )
            if record:
                self.api_key_repo.invalidate(record.id)
                self.db.commit()
            raise LLMProviderError(
                "Your API key is invalid or expired. Please update it in Settings.",
                provider=provider,
                llm_error_type="LLM_KEY_INVALID",
            )
        if "429" in error_str or "rate limit" in error_str:
            raise RateLimitError(
                message="Your provider rate limit was hit. Try again in a moment.",
                retry_after=60,
            )
        if any(s in error_str for s in ("quota", "insufficient_quota", "billing")):
            raise LLMProviderError(
                "Your API account has insufficient credits. Check your provider dashboard.",
                provider=provider,
                llm_error_type="LLM_QUOTA_EXCEEDED",
            )
        if "model" in error_str and (
            "not found" in error_str or "does not exist" in error_str
        ):
            raise LLMProviderError(
                "The selected model is not available. Try a different model in Settings.",
                provider=provider,
                llm_error_type="LLM_MODEL_UNAVAILABLE",
            )
        logger.exception(
            "Unclassified BAML error from provider=%s", provider, exc_info=exc
        )
        raise LLMProviderError(f"AI generation failed: {exc}", provider=provider)
