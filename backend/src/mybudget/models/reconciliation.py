"""
Reconciliation model.

Represents an account reconciliation session.
"""
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class ReconciliationStatus(str, Enum):
    """Reconciliation status enumeration."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Reconciliation(Base):
    """
    Account reconciliation model.

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        account_id: Reference to the account being reconciled
        statement_balance: Balance from the bank statement
        statement_date: Date of the bank statement
        status: IN_PROGRESS or COMPLETED
        adjustment_transaction_id: Optional adjustment transaction if needed
        created_at: Record creation timestamp
        completed_at: When reconciliation was completed
    """

    __tablename__ = "reconciliations"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement_balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 4), nullable=False
    )
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReconciliationStatus] = mapped_column(
        ENUM(ReconciliationStatus, name="reconciliation_status", create_type=True),
        nullable=False,
        default=ReconciliationStatus.IN_PROGRESS,
        insert_default=ReconciliationStatus.IN_PROGRESS,
    )
    adjustment_transaction_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def calculate_cleared_balance(self, cleared_transactions_total: Decimal) -> Decimal:
        """
        Calculate the cleared balance based on cleared transactions.

        This is a helper method - the actual calculation is done in the service
        since it requires database access to sum cleared transactions.

        Args:
            cleared_transactions_total: Sum of all cleared transaction amounts

        Returns:
            The cleared balance (starting balance + cleared transactions)
        """
        # Note: The starting balance comes from the account, which needs
        # to be fetched in the service layer
        return cleared_transactions_total

    def calculate_discrepancy(
        self, cleared_balance: Decimal
    ) -> Decimal:
        """
        Calculate the discrepancy between statement and cleared balance.

        Args:
            cleared_balance: The calculated cleared balance

        Returns:
            The discrepancy (statement_balance - cleared_balance)
        """
        return self.statement_balance - cleared_balance

    def __repr__(self) -> str:
        """Readable representation of Reconciliation."""
        status_str = self.status.value if self.status else "None"
        return f"Reconciliation(id={self.id}, account_id={self.account_id}, statement_balance={self.statement_balance}, status={status_str})"
