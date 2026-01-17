"""
Assignment model.

Represents funds assigned to categories for a specific month.
Per FR-037, assignments are append-only for audit trail.
"""
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DECIMAL

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class Assignment(Base):
    """
    Assignment model.

    Records funds assigned to a category for a specific month.
    Assignments are append-only - to "unassign", create a negative assignment.

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        category_id: Reference to the target category
        amount: Amount assigned (positive) or unassigned (negative)
        month: First day of the month this assignment applies to
        created_at: Creation timestamp
    """

    __tablename__ = "assignments"

    __table_args__ = (
        Index("idx_assignments_category_month", "category_id", "month"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(19, 4),
        nullable=False,
    )
    month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
    )

    def __repr__(self) -> str:
        """Readable representation of Assignment."""
        return f"Assignment(id={self.id}, category_id={self.category_id}, amount={self.amount}, month={self.month})"
