"""Validate user-provided LLM API keys before storage.

Makes a minimal, low-cost API call to each provider to verify
the key is functional. Never logs or exposes the raw key value.
"""

import logging
import re

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_GOOGLE_KEY_RE = re.compile(r"[A-Za-z0-9\-_]+")
_SUPPORTED_PROVIDERS = frozenset({"openai", "google", "anthropic"})


class ApiKeyValidationService:
    """Validates LLM API keys via format checks and live provider calls."""

    def _check_format(self, provider: str, api_key: str) -> tuple[bool, str]:
        if provider not in _SUPPORTED_PROVIDERS:
            return (False, "Unsupported provider")
        if not api_key or not api_key.strip():
            return (False, "API key is empty")
        if provider == "openai":
            if not api_key.startswith("sk-") or len(api_key) <= 20:
                return (False, "Invalid key format for OpenAI")
        elif provider == "anthropic":
            if not api_key.startswith("sk-ant-") or len(api_key) <= 20:
                return (False, "Invalid key format for Anthropic")
        elif provider == "google":
            if len(api_key) < 30 or not _GOOGLE_KEY_RE.fullmatch(api_key):
                return (False, "Invalid key format for Google")
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

    async def validate(self, provider: str, api_key: str) -> tuple[bool, str]:
        """Validate a provider API key. Returns ``(is_valid, error_msg)``."""
        provider = provider.lower().strip()
        ok, msg = self._check_format(provider, api_key)
        if not ok:
            return (False, msg)

        dispatch = {
            "openai": self._validate_openai,
            "google": self._validate_google,
            "anthropic": self._validate_anthropic,
        }
        handler = dispatch.get(provider)
        if handler is None:
            return (False, "Unsupported provider")

        try:
            return await handler(api_key)
        except httpx.TimeoutException:
            logger.warning("Validation timed out for provider=%s", provider)
            return (False, "Provider unreachable")
        except Exception:
            logger.exception("Validation failed for provider=%s", provider)
            return (False, "Validation failed")
