"""
CategorizationRule model.

Represents an auto-categorization rule for transactions.
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class CategorizationRule(Base):
    """
    Auto-categorization rule model.

    Used to automatically assign categories to transactions based on payee pattern matching.

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        payee_pattern: Pattern to match against transaction payees
        category_id: Reference to the category to assign
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "categorization_rules"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payee_pattern: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
        onupdate=utc_now,
    )

    def matches(self, payee: str) -> bool:
        """
        Check if payee matches this rule pattern.

        MVP implementation: simple case-insensitive substring match.
        Future: support wildcards, regex.

        Args:
            payee: Transaction payee to match against

        Returns:
            True if the pattern matches the payee
        """
        return self.payee_pattern.lower() in payee.lower()

    def __repr__(self) -> str:
        """Readable representation of CategorizationRule."""
        return f"CategorizationRule(id={self.id}, pattern={self.payee_pattern!r})"
