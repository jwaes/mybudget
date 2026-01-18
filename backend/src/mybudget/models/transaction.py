"""
Transaction model.

Represents a financial transaction on an account.
"""
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class TransactionState(str, Enum):
    """Transaction state enumeration."""

    INBOX = "INBOX"
    APPROVED = "APPROVED"
    CLEARED = "CLEARED"


class CategorizationSource(str, Enum):
    """Source of transaction categorization.

    Used to track how a transaction was categorized for analytics
    and future ML improvements.

    Attributes:
        MANUAL: User manually selected the category
        RULE: Category was assigned by a matching rule
        ML_SUGGESTED: Category was suggested by ML and user accepted
    """

    MANUAL = "MANUAL"
    RULE = "RULE"
    ML_SUGGESTED = "ML_SUGGESTED"


class Transaction(Base):
    """
    Financial transaction model.

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        account_id: Reference to the account
        category_id: Optional reference to the budget category
        date: Transaction date (not import date)
        payee: Name of the merchant/payee
        amount: Transaction amount (positive=inflow, negative=outflow)
        memo: Optional transaction memo
        state: INBOX, APPROVED, or CLEARED
        created_at: Record creation timestamp
        updated_at: Last modification timestamp
        approved_at: When state changed to APPROVED
        cleared_at: When marked cleared during reconciliation
    """

    __tablename__ = "transactions"

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
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payee: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[TransactionState] = mapped_column(
        ENUM(TransactionState, name="transaction_state", create_type=True),
        nullable=False,
        insert_default=TransactionState.INBOX,
        index=True,
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
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cleared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    categorization_source: Mapped[CategorizationSource | None] = mapped_column(
        ENUM(CategorizationSource, name="categorization_source", create_type=True),
        nullable=True,
        index=True,
    )
    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_transactions_confidence_score_range",
        ),
    )

    def __repr__(self) -> str:
        """Readable representation of Transaction."""
        state_str = self.state.value if self.state else "None"
        return f"Transaction(id={self.id}, date={self.date}, payee={self.payee!r}, amount={self.amount}, state={state_str})"
