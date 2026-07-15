"""Central registry of supported LLM providers for BYOK.

Single source of truth for provider metadata — replaces what used to be
duplicated across schemas, api_key_service, api_key_validation_service, and
baml_client_factory. This module is a pure leaf (dataclasses + stdlib only,
no DB/session imports) so it's safe to import from the schema layer. Lives
under app/utils/ rather than app/services/ specifically so importing it does
not trigger app/services/__init__.py's eager imports, which would otherwise
create a schema -> services -> repositories -> schemas circular import.
"""

from dataclasses import dataclass
from typing import Literal, get_args

ProviderSlug = Literal[
    "openai",
    "openai_responses",
    "anthropic",
    "google",
    "azure_openai",
    "openai_generic",
    "microsoft_foundry",
    "ollama",
]


@dataclass(frozen=True)
class ProviderSpec:
    """Everything the BYOK stack needs to know about one LLM provider."""

    slug: str
    label: str
    baml_provider: str
    requires_api_key: bool
    requires_base_url: bool
    requires_api_version: bool
    default_base_url: str | None
    free_form_models: bool
    curated_models: tuple[str, ...]
    default_model: str | None
    key_format_hint: str | None
    live_probe: bool


_OPENAI_MODELS: tuple[str, ...] = (
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.4-mini",
)
_ANTHROPIC_MODELS: tuple[str, ...] = ("claude-opus-4-8", "claude-sonnet-5")
_GOOGLE_MODELS: tuple[str, ...] = (
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
)

PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        slug="openai",
        label="OpenAI",
        baml_provider="openai",
        requires_api_key=True,
        requires_base_url=False,
        requires_api_version=False,
        default_base_url="https://api.openai.com/v1",
        free_form_models=False,
        curated_models=_OPENAI_MODELS,
        default_model="gpt-5.4-mini",
        key_format_hint="Starts with 'sk-'",
        live_probe=True,
    ),
    "openai_responses": ProviderSpec(
        slug="openai_responses",
        label="OpenAI (Responses API)",
        baml_provider="openai-responses",
        requires_api_key=True,
        requires_base_url=False,
        requires_api_version=False,
        default_base_url="https://api.openai.com/v1",
        free_form_models=False,
        curated_models=_OPENAI_MODELS,
        default_model="gpt-5.4-mini",
        key_format_hint="Starts with 'sk-' (same key as OpenAI)",
        live_probe=True,
    ),
    "anthropic": ProviderSpec(
        slug="anthropic",
        label="Anthropic",
        baml_provider="anthropic",
        requires_api_key=True,
        requires_base_url=False,
        requires_api_version=False,
        default_base_url="https://api.anthropic.com",
        free_form_models=False,
        curated_models=_ANTHROPIC_MODELS,
        default_model="claude-sonnet-5",
        key_format_hint="Starts with 'sk-ant-'",
        live_probe=True,
    ),
    "google": ProviderSpec(
        slug="google",
        label="Google Gemini",
        baml_provider="google-ai",
        requires_api_key=True,
        requires_base_url=False,
        requires_api_version=False,
        default_base_url="https://generativelanguage.googleapis.com/v1beta",
        free_form_models=False,
        curated_models=_GOOGLE_MODELS,
        default_model="gemini-3.5-flash",
        key_format_hint="Alphanumeric key, 30+ characters",
        live_probe=True,
    ),
    "azure_openai": ProviderSpec(
        slug="azure_openai",
        label="Azure OpenAI",
        baml_provider="azure-openai",
        requires_api_key=True,
        requires_base_url=True,
        requires_api_version=True,
        default_base_url=None,
        free_form_models=True,
        curated_models=(),
        default_model=None,
        key_format_hint="Azure portal API key (no fixed prefix)",
        live_probe=False,
    ),
    "openai_generic": ProviderSpec(
        slug="openai_generic",
        label="Custom Endpoint (OpenAI-Compatible)",
        baml_provider="openai-generic",
        requires_api_key=True,
        requires_base_url=True,
        requires_api_version=False,
        default_base_url=None,
        free_form_models=True,
        curated_models=(),
        default_model=None,
        key_format_hint="Provider-specific key (no fixed prefix)",
        live_probe=False,
    ),
    "microsoft_foundry": ProviderSpec(
        slug="microsoft_foundry",
        label="Microsoft Foundry",
        baml_provider="openai-generic",
        requires_api_key=True,
        requires_base_url=True,
        requires_api_version=False,
        default_base_url=None,
        free_form_models=True,
        curated_models=(),
        default_model=None,
        key_format_hint="Azure AI Foundry API key (no fixed prefix)",
        live_probe=False,
    ),
    "ollama": ProviderSpec(
        slug="ollama",
        label="Ollama",
        baml_provider="openai-generic",
        requires_api_key=False,
        requires_base_url=True,
        requires_api_version=False,
        # Deliberately None, not BAML's own "http://localhost:11434/v1" default:
        # this backend runs on Fly.io and can never reach a literal localhost.
        # Surfacing that default would let a user "successfully" save a config
        # that can never work in production.
        default_base_url=None,
        free_form_models=True,
        curated_models=(),
        default_model=None,
        key_format_hint="Optional bearer token — only needed for proxied/tunneled/Ollama Cloud setups",
        live_probe=False,
    ),
}

assert set(get_args(ProviderSlug)) == set(
    PROVIDERS.keys()
), "ProviderSlug and PROVIDERS registry have drifted out of sync"


def get_provider_spec(slug: str) -> ProviderSpec:
    """Look up a provider's spec by slug. Raises ValueError on an unknown slug."""
    try:
        return PROVIDERS[slug]
    except KeyError:
        raise ValueError(f"Unknown provider slug: {slug!r}") from None
