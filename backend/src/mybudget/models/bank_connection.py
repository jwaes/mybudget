"""
Bank connection models for external bank integrations.
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mybudget.db.base import Base

if TYPE_CHECKING:
    from mybudget.models.account import Account
    from mybudget.models.user import User


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class BankConnectionStatus(str, Enum):
    """Status of a bank connection."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"
    PENDING_REAUTH = "PENDING_REAUTH"


class LinkedAccountType(str, Enum):
    """Type of linked bank account."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT = "CREDIT"


class SyncJobStatus(str, Enum):
    """Status of a sync job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SyncTriggerType(str, Enum):
    """What triggered the sync job."""

    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
    INITIAL = "INITIAL"


class BankConnection(Base):
    """Represents a connection to an external bank via a provider."""

    __tablename__ = "bank_connections"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_connection_id: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_id: Mapped[str] = mapped_column(String(100), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[BankConnectionStatus] = mapped_column(
        ENUM(BankConnectionStatus, name="bank_connection_status", create_type=True),
        nullable=False,
        default=BankConnectionStatus.PENDING,
        insert_default=BankConnectionStatus.PENDING,
    )
    status_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    access_valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships
    user: Mapped["User"] = relationship(back_populates="bank_connections")
    linked_accounts: Mapped[list["LinkedAccount"]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )
    sync_jobs: Mapped[list["SyncJob"]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )

    def is_access_expiring_soon(self, days: int = 7) -> bool:
        """Check if access token expires within the given number of days."""
        if self.access_valid_until is None:
            return False
        threshold = datetime.now(UTC) + timedelta(days=days)
        return self.access_valid_until < threshold


class LinkedAccount(Base):
    """Represents a specific account within a bank connection."""

    __tablename__ = "linked_accounts"

    connection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bank_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_number_masked: Mapped[str | None] = mapped_column(String(50), nullable=True)
    account_type: Mapped[LinkedAccountType | None] = mapped_column(
        ENUM(LinkedAccountType, name="linked_account_type", create_type=True),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", insert_default="EUR")
    balance: Mapped[Decimal | None] = mapped_column(Numeric(19, 4), nullable=True)
    balance_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, insert_default=True)
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

    # Relationships
    connection: Mapped["BankConnection"] = relationship(back_populates="linked_accounts")
    account: Mapped["Account | None"] = relationship()


class SyncJob(Base):
    """Represents a transaction sync operation."""

    __tablename__ = "sync_jobs"

    connection_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bank_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    linked_account_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("linked_accounts.id", ondelete="CASCADE"),
        nullable=True,
    )
    status: Mapped[SyncJobStatus] = mapped_column(
        ENUM(SyncJobStatus, name="sync_job_status", create_type=True),
        nullable=False,
        default=SyncJobStatus.PENDING,
        insert_default=SyncJobStatus.PENDING,
    )
    trigger_type: Mapped[SyncTriggerType] = mapped_column(
        ENUM(SyncTriggerType, name="sync_trigger_type", create_type=True),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    transactions_fetched: Mapped[int] = mapped_column(nullable=False, default=0, insert_default=0)
    transactions_imported: Mapped[int] = mapped_column(nullable=False, default=0, insert_default=0)
    transactions_duplicates: Mapped[int] = mapped_column(nullable=False, default=0, insert_default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
    )

    # Relationships
    connection: Mapped["BankConnection"] = relationship(back_populates="sync_jobs")
    linked_account: Mapped["LinkedAccount | None"] = relationship()
