"""AES-256-GCM encryption service for API key storage.

Encrypts user-provided API keys before persisting them to the database.
Uses a process-level singleton keyed from API_KEY_ENCRYPTION_SECRET.

Future: add per-user AAD (additional authenticated data) to bind ciphertext
to a user ID and prevent cross-user ciphertext transplant attacks.
Key rotation migration pattern documented in issue #11.
"""

import base64
import logging
import os

from cryptography.exceptions import InvalidTag  # noqa: F401 — re-exported for callers
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

logger = logging.getLogger(__name__)

_NONCE_BYTES = 12
_KEY_BYTES = 32


class EncryptionService:
    """AES-256-GCM authenticated encryption for API keys."""

    def __init__(self) -> None:
        try:
            key_bytes = base64.b64decode(settings.encryption_key)
        except Exception as exc:
            raise ValueError(
                "API_KEY_ENCRYPTION_SECRET is not valid base64"
            ) from exc
        if len(key_bytes) != _KEY_BYTES:
            raise ValueError(
                f"API_KEY_ENCRYPTION_SECRET must decode to exactly {_KEY_BYTES} "
                f"bytes (256 bits), got {len(key_bytes)}"
            )
        self._aesgcm = AESGCM(key_bytes)

    def encrypt(self, plaintext: str) -> tuple[str, str]:
        """Encrypt *plaintext* and return ``(ciphertext_b64, nonce_b64)``."""
        nonce = os.urandom(_NONCE_BYTES)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        return (
            base64.b64encode(ciphertext).decode(),
            base64.b64encode(nonce).decode(),
        )

    def decrypt(self, ciphertext_b64: str, nonce_b64: str) -> str:
        """Decrypt and return the original plaintext.

        Raises ``cryptography.exceptions.InvalidTag`` on tampered data.
        """
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        return self._aesgcm.decrypt(nonce, ciphertext, None).decode()


encryption_service = EncryptionService()
