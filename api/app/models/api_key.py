"""User API key model for BYOK (Bring Your Own Key) feature"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserApiKey(Base):
    """Stores encrypted LLM API keys per user per provider"""
    __tablename__ = "user_api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    encryption_nonce: Mapped[str] = mapped_column(Text, nullable=False)
    key_hint: Mapped[str] = mapped_column(String(8), nullable=False)
    is_valid: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default='true', nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
        CheckConstraint(
            "provider IN ('openai', 'google', 'anthropic')",
            name="ck_valid_provider",
        ),
        Index("idx_user_api_keys_user_id", "user_id"),
    )

    # Relationships
    user = relationship("User", back_populates="api_keys")
