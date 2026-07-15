"""Best-effort SSRF guard for user-supplied LLM endpoint base_urls.

Used when a BYOK user configures a custom/self-hosted provider (Azure OpenAI,
a generic OpenAI-compatible endpoint, Microsoft Foundry, or Ollama) — the
backend makes real outbound requests to this URL server-side during
generation, so an unchecked value would let a user point the server at
internal infrastructure.

This is explicitly NOT a complete SSRF fix:
- DNS rebinding is not defended against — a hostname resolving to a public IP
  at save time could repoint to an internal IP by generation time. Only a
  request-time, resolve-then-connect guard inside the actual HTTP client
  could close that, and this app does not control BAML's Rust HTTP layer.
- Numeric/octal/hex IP obfuscation (e.g. "http://2130706433/") is not caught,
  since ipaddress.ip_address() only parses standard dotted-quad/IPv6 forms.
Both gaps are accepted here to avoid over-engineering a guard that can never
be airtight without controlling the actual outbound HTTP client.
"""

import ipaddress
from urllib.parse import urlsplit


def is_safe_base_url(url: str) -> tuple[bool, str]:
    """Check a user-supplied base_url is not obviously pointed at internal
    infrastructure. Returns ``(is_safe, error_message)``.
    """
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        return False, "URL must use http or https"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a host"

    # Fly.io can never reach a literal localhost — this only forecloses a
    # config that could never work, not a legitimate use case.
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return False, "localhost is not reachable from this server"

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        # Not a literal IP — a DNS name. See module docstring: DNS rebinding
        # past this point is a known, accepted residual gap.
        return True, ""

    if (
        ip.is_loopback
        or ip.is_link_local  # covers the 169.254.169.254 cloud metadata address
        or ip.is_private
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return False, "URL resolves to a non-public address"

    return True, ""
