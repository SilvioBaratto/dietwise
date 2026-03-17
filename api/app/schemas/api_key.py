"""Pydantic schemas for BYOK API key management."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_PROVIDERS = Literal["openai", "anthropic", "google"]


class ApiKeySaveRequest(BaseModel):
    provider: _PROVIDERS
    api_key: str = Field(min_length=10, max_length=512)


class ApiKeyResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    key_hint: str
    is_valid: bool
    updated_at: datetime


class ProviderPreferencesRequest(BaseModel):
    provider: _PROVIDERS
    model: str = Field(min_length=1, max_length=100)


class AvailableModelsResponse(BaseModel):
    openai: list[str]
    anthropic: list[str]
    google: list[str]


class ValidateKeyRequest(BaseModel):
    provider: _PROVIDERS
    api_key: str = Field(min_length=10, max_length=512)


class ValidateKeyResponse(BaseModel):
    provider: str
    is_valid: bool
    error: str | None = None


class ProviderPreferencesResponse(BaseModel):
    provider: str | None
    model: str | None
