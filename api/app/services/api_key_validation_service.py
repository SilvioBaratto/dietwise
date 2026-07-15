"""Validate user-provided LLM API keys before storage.

Makes a minimal, low-cost API call to each provider to verify
the key is functional. Never logs or exposes the raw key value.

For self-hosted/custom-endpoint providers (azure_openai, openai_generic,
microsoft_foundry, ollama), no live probe is attempted — arbitrary endpoints
can't be reliably probed with one generic strategy, and this backend can
never reach a bare localhost anyway. Format checks are the final answer for
those; real validity is proven on first actual generation call, where
BamlClientFactory.handle_baml_error() already auto-invalidates a bad
key/config on a real 401.
"""

import logging
import re

import httpx

from app.utils.llm_providers import PROVIDERS, get_provider_spec
from app.utils.url_safety import is_safe_base_url

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_GOOGLE_KEY_RE = re.compile(r"[A-Za-z0-9\-_]+")  # legacy "AIza..." standard keys
_GOOGLE_AUTH_KEY_RE = re.compile(r"AQ\.[A-Za-z0-9\-_]+")  # new "AQ." auth keys (2026 rollout)
_AZURE_API_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(-preview)?$")


class ApiKeyValidationService:
    """Validates LLM API keys via format checks and live provider calls."""

    def _check_format(
        self,
        provider: str,
        api_key: str | None,
        base_url: str | None,
        api_version: str | None,
    ) -> tuple[bool, str]:
        if provider not in PROVIDERS:
            return (False, "Unsupported provider")
        spec = get_provider_spec(provider)

        if spec.requires_api_key and (not api_key or not api_key.strip()):
            return (False, "API key is empty")
        if api_key and provider in ("openai", "openai_responses"):
            if not api_key.startswith("sk-") or len(api_key) <= 20:
                return (False, "Invalid key format for OpenAI")
        elif api_key and provider == "anthropic":
            if not api_key.startswith("sk-ant-") or len(api_key) <= 20:
                return (False, "Invalid key format for Anthropic")
        elif provider == "google" and not (
            api_key
            and (
                (len(api_key) >= 30 and _GOOGLE_KEY_RE.fullmatch(api_key))
                or _GOOGLE_AUTH_KEY_RE.fullmatch(api_key)
            )
        ):
            return (False, "Invalid key format for Google")

        if spec.requires_base_url:
            if not base_url:
                return (False, "base_url is required for this provider")
            ok, msg = is_safe_base_url(base_url)
            if not ok:
                return (False, msg)

        if spec.requires_api_version:
            if not api_version:
                return (False, "api_version is required for this provider")
            if not _AZURE_API_VERSION_RE.match(api_version):
                logger.warning(
                    "Unusual Azure api_version format: %s (allowing anyway)",
                    api_version,
                )

        return (True, "")

    async def _validate_openai(self, api_key: str) -> tuple[bool, str]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        return self._map_status(resp.status_code)

    async def _validate_google(self, api_key: str) -> tuple[bool, str]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://generativelanguage.googleapis.com/v1/models",
                params={"key": api_key},
            )
        return self._map_status(resp.status_code)

    async def _validate_anthropic(self, api_key: str) -> tuple[bool, str]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
        return self._map_status(resp.status_code)

    @staticmethod
    def _map_status(status_code: int) -> tuple[bool, str]:
        if 200 <= status_code < 300:
            return (True, "")
        if status_code in (401, 403):
            return (False, "Invalid API key")
        if status_code == 429:
            return (False, "Rate limited — key may be valid, try again")
        return (False, "Provider returned unexpected error")

    async def validate(
        self,
        provider: str,
        api_key: str | None,
        base_url: str | None = None,
        api_version: str | None = None,
    ) -> tuple[bool, str]:
        """Validate a provider API key/config. Returns ``(is_valid, error_msg)``."""
        provider = provider.lower().strip()
        ok, msg = self._check_format(provider, api_key, base_url, api_version)
        if not ok:
            return (False, msg)

        spec = get_provider_spec(provider)
        if not spec.live_probe:
            # Self-hosted/custom-endpoint providers: format check is the final
            # answer, see module docstring.
            return (True, "")

        dispatch = {
            "openai": self._validate_openai,
            "openai_responses": self._validate_openai,
            "google": self._validate_google,
            "anthropic": self._validate_anthropic,
        }
        handler = dispatch.get(provider)
        if handler is None:
            return (False, "Unsupported provider")

        # _check_format already enforced non-empty api_key for every
        # live_probe provider (all require_api_key=True) — narrow the type.
        assert api_key is not None

        try:
            return await handler(api_key)
        except httpx.TimeoutException:
            logger.warning("Validation timed out for provider=%s", provider)
            return (False, "Provider unreachable")
        except Exception:
            logger.exception("Validation failed for provider=%s", provider)
            return (False, "Validation failed")
