"""
CategoryTarget model.

Represents a spending target for a budget category.
Supports three types: Monthly Needed, Target Balance, and Target by Date.
"""
from datetime import UTC, date, datetime
from decimal import ROUND_CEILING, Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DECIMAL

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class TargetType(str, Enum):
    """Target type enumeration."""

    MONTHLY_NEEDED = "MONTHLY_NEEDED"
    TARGET_BALANCE = "TARGET_BALANCE"
    TARGET_BY_DATE = "TARGET_BY_DATE"


class CategoryTarget(Base):
    """
    Category spending target model.

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        category_id: Reference to the target category (unique)
        target_type: Type of target (MONTHLY_NEEDED, TARGET_BALANCE, TARGET_BY_DATE)
        amount: Target amount (must be > 0)
        target_date: Required for TARGET_BY_DATE, null otherwise
        created_at: Target creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "category_targets"

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_positive_amount"),
        CheckConstraint(
            "(target_type = 'TARGET_BY_DATE' AND target_date IS NOT NULL) OR "
            "(target_type != 'TARGET_BY_DATE' AND target_date IS NULL)",
            name="check_target_date_constraint",
        ),
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
        unique=True,  # One target per category
        index=True,
    )
    target_type: Mapped[TargetType] = mapped_column(
        ENUM(TargetType, name="target_type", create_type=True),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(19, 4),
        nullable=False,
    )
    target_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
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

    def calculate_underfunded(
        self,
        funded_this_month: Decimal,
        available_now: Decimal,
        current_month: date,
    ) -> Decimal:
        """
        Calculate underfunded amount based on target type.

        Per FR-028 formulas:
        - Monthly Needed: max(0, target_amount - funded_this_month)
        - Target Balance: max(0, target_amount - available_now)
        - Target by Date: max(0, suggested_monthly - funded_this_month)

        Args:
            funded_this_month: Sum of assignments for this month
            available_now: Current available balance (rollover + funded - activity)
            current_month: The month for calculation (first day)

        Returns:
            Amount needed to meet target this month
        """
        if self.target_type == TargetType.MONTHLY_NEEDED:
            return max(Decimal("0"), self.amount - funded_this_month)

        elif self.target_type == TargetType.TARGET_BALANCE:
            return max(Decimal("0"), self.amount - available_now)

        elif self.target_type == TargetType.TARGET_BY_DATE:
            months_left = self._calculate_months_left(current_month)

            # How much more is needed to reach the target
            needed_now = max(Decimal("0"), self.amount - available_now)

            if needed_now == Decimal("0"):
                return Decimal("0")

            # Calculate suggested monthly amount
            suggested_monthly = (needed_now / months_left).quantize(
                Decimal("0.01"), rounding=ROUND_CEILING
            )

            return max(Decimal("0"), suggested_monthly - funded_this_month)

        return Decimal("0")

    def _calculate_months_left(self, current_month: date) -> int:
        """
        Calculate months from current_month to target_date (inclusive).

        Args:
            current_month: Current month (first day)

        Returns:
            Number of months remaining (minimum 1)
        """
        if not self.target_date:
            return 1

        # Calculate month difference including current month
        months = (
            (self.target_date.year - current_month.year) * 12
            + (self.target_date.month - current_month.month)
            + 1  # Include both current and target month
        )

        # Always at least 1 month (prevent division by zero)
        return max(1, months)

    def get_suggested_monthly(self, available_now: Decimal, current_month: date) -> Decimal | None:
        """
        Get suggested monthly amount for TARGET_BY_DATE targets.

        Args:
            available_now: Current available balance
            current_month: Current month (first day)

        Returns:
            Suggested monthly amount or None for non-date targets
        """
        if self.target_type != TargetType.TARGET_BY_DATE:
            return None

        months_left = self._calculate_months_left(current_month)
        needed_now = max(Decimal("0"), self.amount - available_now)

        if needed_now == Decimal("0"):
            return Decimal("0")

        return (needed_now / months_left).quantize(Decimal("0.01"), rounding=ROUND_CEILING)

    def __repr__(self) -> str:
        """Readable representation of CategoryTarget."""
        return (
            f"CategoryTarget(id={self.id}, type={self.target_type.value}, "
            f"amount={self.amount}, date={self.target_date})"
        )
