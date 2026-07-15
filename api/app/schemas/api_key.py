"""Pydantic schemas for BYOK API key management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.utils.llm_providers import ProviderSlug, get_provider_spec
from app.utils.url_safety import is_safe_base_url


class _ProviderConnectionRequest(BaseModel):
    """Shared shape for anything that carries a provider + its connection info.

    Requiredness of api_key/base_url/api_version is provider-dependent (e.g.
    Ollama's key is optional, Azure OpenAI requires base_url + api_version) —
    enforced here against the single source of truth in llm_providers.PROVIDERS
    rather than duplicating per-provider rules in every request schema.
    """

    provider: ProviderSlug
    api_key: str | None = Field(default=None, min_length=10, max_length=512)
    base_url: str | None = Field(default=None, min_length=1, max_length=2048)
    api_version: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def _validate_provider_requirements(self) -> "_ProviderConnectionRequest":
        spec = get_provider_spec(self.provider)
        if spec.requires_api_key and not self.api_key:
            raise ValueError(f"{spec.label} requires an API key")
        if spec.requires_base_url and not self.base_url:
            raise ValueError(f"{spec.label} requires a base_url")
        if spec.requires_api_version and not self.api_version:
            raise ValueError(f"{spec.label} requires an api_version")
        if self.base_url:
            ok, msg = is_safe_base_url(self.base_url)
            if not ok:
                raise ValueError(f"base_url is not allowed: {msg}")
        return self


class ApiKeySaveRequest(_ProviderConnectionRequest):
    pass


class ValidateKeyRequest(_ProviderConnectionRequest):
    pass


class ApiKeyResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    key_hint: str
    is_valid: bool
    updated_at: datetime
    base_url: str | None = None
    api_version: str | None = None


class ProviderPreferencesRequest(BaseModel):
    provider: ProviderSlug
    model: str = Field(min_length=1, max_length=100)


class ProviderInfo(BaseModel):
    slug: str
    label: str
    requires_api_key: bool
    requires_base_url: bool
    requires_api_version: bool
    default_base_url: str | None
    free_form_models: bool
    models: list[str]
    default_model: str | None
    key_format_hint: str | None


class ProvidersResponse(BaseModel):
    providers: list[ProviderInfo]


class ValidateKeyResponse(BaseModel):
    provider: str
    is_valid: bool
    error: str | None = None


class ProviderPreferencesResponse(BaseModel):
    provider: str | None
    model: str | None
