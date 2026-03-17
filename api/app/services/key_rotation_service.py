"""Key rotation service for AES-256-GCM encrypted API keys.

Run via management command — not exposed as a REST endpoint.
Usage: fly ssh console -C "python -m app.scripts.rotate_keys"
"""

import logging

from sqlalchemy.orm import Session

from app.repositories.api_key_repository import ApiKeyRepository
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class KeyRotationService:
    def __init__(
        self,
        db: Session,
        old_enc: EncryptionService,
        new_enc: EncryptionService,
    ) -> None:
        self.db = db
        self.old_enc = old_enc
        self.new_enc = new_enc
        self.repo = ApiKeyRepository(db)

    def rotate_all_keys(self, batch_size: int = 100) -> dict[str, int]:
        """Re-encrypt all stored keys from old_enc to new_enc."""
        counts = {"rotated": 0, "failed": 0}
        records = self.repo.get_all_for_rotation()

        for i, record in enumerate(records):
            try:
                plaintext = self.old_enc.decrypt(
                    record.encrypted_key, record.encryption_nonce
                )
                new_ciphertext, new_nonce = self.new_enc.encrypt(plaintext)
                record.encrypted_key = new_ciphertext
                record.encryption_nonce = new_nonce
                counts["rotated"] += 1
                logger.info(
                    "api_key_event",
                    extra={
                        "event": "api_key_rotated",
                        "user_id": record.user_id,
                        "provider": record.provider,
                        "key_hint": record.key_hint,
                    },
                )
            except Exception:
                logger.exception(
                    "Key rotation failed for record id=%s", record.id
                )
                counts["failed"] += 1
                continue

            if (i + 1) % batch_size == 0:
                self.db.commit()

        self.db.commit()
        return counts
