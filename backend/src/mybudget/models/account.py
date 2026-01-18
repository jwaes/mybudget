"""
Account model.

Represents a bank checking or savings account.
"""
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class AccountType(str, Enum):
    """Account type enumeration."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"


class SyncStatus(str, Enum):
    """Account sync status enumeration."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    NEVER_SYNCED = "NEVER_SYNCED"


class Account(Base):
    """
    Bank account model.

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        name: Account display name (e.g., "ING Checking")
        account_type: CHECKING or SAVINGS
        balance: Current account balance
        initial_balance: Starting balance when account was created
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "accounts"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(
        ENUM(AccountType, name="account_type", create_type=True),
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
        nullable=False,
        insert_default=Decimal("0"),
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(19, 4),
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
    sync_status: Mapped[SyncStatus] = mapped_column(
        ENUM(SyncStatus, name="sync_status", create_type=True),
        nullable=False,
        insert_default=SyncStatus.NEVER_SYNCED,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sync_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    def __repr__(self) -> str:
        """Readable representation of Account."""
        return f"Account(id={self.id}, name={self.name!r}, type={self.account_type.value}, balance={self.balance})"
