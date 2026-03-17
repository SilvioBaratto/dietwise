"""Rotate the master encryption key for all stored BYOK API keys.

Usage:
    OLD_KEY=<old_base64> NEW_KEY=<new_base64> python scripts/rotate_encryption_key.py

Steps:
    1. Read all UserApiKey rows
    2. Decrypt each with OLD_KEY
    3. Re-encrypt each with NEW_KEY
    4. Update rows in a single transaction
    5. Output count of rotated keys
"""

import base64
import os
import sys

# Allow imports from the api package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import database_manager  # noqa: E402
from app.models.api_key import UserApiKey  # noqa: E402

_NONCE_BYTES = 12
_KEY_BYTES = 32


def build_aesgcm(b64_key: str, label: str) -> AESGCM:
    """Validate a base64-encoded 256-bit key and return an AESGCM cipher."""
    try:
        key_bytes = base64.b64decode(b64_key)
    except Exception as exc:
        raise SystemExit(f"{label} is not valid base64: {exc}") from exc
    if len(key_bytes) != _KEY_BYTES:
        raise SystemExit(
            f"{label} must decode to {_KEY_BYTES} bytes, got {len(key_bytes)}"
        )
    return AESGCM(key_bytes)


def rotate_all(session, old_cipher: AESGCM, new_cipher: AESGCM) -> int:
    """Re-encrypt every UserApiKey row from old_cipher to new_cipher.

    Uses a two-phase approach: decrypt ALL keys first (verify phase),
    then re-encrypt and write ALL in a single transaction.  If any
    decrypt fails the function aborts before any row is modified.
    """
    rows = session.execute(select(UserApiKey)).scalars().all()

    # Phase 1 — verify: decrypt every key with the old cipher
    decrypted: list[tuple[UserApiKey, bytes]] = []
    for row in rows:
        ciphertext = base64.b64decode(row.encrypted_key)
        nonce = base64.b64decode(row.encryption_nonce)
        plaintext = old_cipher.decrypt(nonce, ciphertext, None)
        decrypted.append((row, plaintext))

    # Phase 2 — re-encrypt: write new ciphertext in a single transaction
    for row, plaintext in decrypted:
        new_nonce = os.urandom(_NONCE_BYTES)
        new_ciphertext = new_cipher.encrypt(new_nonce, plaintext, None)
        row.encrypted_key = base64.b64encode(new_ciphertext).decode()
        row.encryption_nonce = base64.b64encode(new_nonce).decode()

    session.commit()
    return len(rows)


def main() -> None:
    """Entry point: read env vars, bootstrap DB, run rotation."""
    old_b64 = os.environ.get("OLD_KEY")
    new_b64 = os.environ.get("NEW_KEY")
    if not old_b64 or not new_b64:
        raise SystemExit("Both OLD_KEY and NEW_KEY env vars are required.")

    old_cipher = build_aesgcm(old_b64, "OLD_KEY")
    new_cipher = build_aesgcm(new_b64, "NEW_KEY")

    database_manager.initialize()
    with database_manager.get_session() as session:
        try:
            count = rotate_all(session, old_cipher, new_cipher)
        except Exception as exc:
            print(f"Rotation failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    print(f"Rotated {count} key(s) successfully.")


if __name__ == "__main__":
    main()
