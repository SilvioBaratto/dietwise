"""API key repository for data access operations"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserApiKey


class ApiKeyRepository:
    """Repository for UserApiKey operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_provider(self, user_id: str, provider: str) -> UserApiKey | None:
        """Get API key by user ID and provider"""
        stmt = select(UserApiKey).where(
            UserApiKey.user_id == user_id,
            UserApiKey.provider == provider,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_all_by_user(self, user_id: str) -> list[UserApiKey]:
        """Get all API keys for a user"""
        stmt = (
            select(UserApiKey)
            .where(UserApiKey.user_id == user_id)
            .order_by(UserApiKey.created_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def create(
        self,
        user_id: str,
        provider: str,
        encrypted_key: str,
        encryption_nonce: str,
        key_hint: str,
    ) -> UserApiKey:
        """Create or update API key for user and provider (upsert)"""
        existing = self.get_by_user_and_provider(user_id, provider)
        if existing:
            existing.encrypted_key = encrypted_key
            existing.encryption_nonce = encryption_nonce
            existing.key_hint = key_hint
            existing.is_valid = True
            self.db.flush()
            self.db.refresh(existing)
            return existing

        api_key = UserApiKey(
            id=str(uuid.uuid4()),
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypted_key,
            encryption_nonce=encryption_nonce,
            key_hint=key_hint,
        )
        self.db.add(api_key)
        self.db.flush()
        self.db.refresh(api_key)
        return api_key

    def update(
        self,
        key_id: str,
        user_id: str,
        encrypted_key: str,
        encryption_nonce: str,
        key_hint: str,
    ) -> UserApiKey | None:
        """Update an existing API key by ID, scoped to user"""
        stmt = select(UserApiKey).where(
            UserApiKey.id == key_id,
            UserApiKey.user_id == user_id,
        )
        result = self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        if not api_key:
            return None

        api_key.encrypted_key = encrypted_key
        api_key.encryption_nonce = encryption_nonce
        api_key.key_hint = key_hint
        self.db.flush()
        self.db.refresh(api_key)
        return api_key

    def delete_by_user_and_provider(self, user_id: str, provider: str) -> bool:
        """Delete API key by user ID and provider"""
        api_key = self.get_by_user_and_provider(user_id, provider)
        if not api_key:
            return False

        self.db.delete(api_key)
        self.db.flush()
        return True

    def get_all_for_rotation(self) -> list[UserApiKey]:
        """Return all rows for key rotation. Admin-only operation."""
        stmt = select(UserApiKey).order_by(UserApiKey.created_at)
        return list(self.db.execute(stmt).scalars().all())

    def invalidate(self, key_id: str) -> None:
        """Mark an API key as invalid"""
        stmt = select(UserApiKey).where(UserApiKey.id == key_id)
        result = self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        if api_key:
            api_key.is_valid = False
            self.db.flush()
