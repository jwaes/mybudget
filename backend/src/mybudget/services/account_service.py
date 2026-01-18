"""
Account service for business logic operations.
"""
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.account import Account, SyncStatus
from mybudget.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    """Service for account operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_account(
        self, user_id: UUID, data: AccountCreate
    ) -> Account:
        """
        Create a new account.

        Args:
            user_id: Owner user ID
            data: Account creation data

        Returns:
            Created account
        """
        account = Account(
            user_id=user_id,
            name=data.name,
            account_type=data.account_type,
            initial_balance=data.initial_balance,
            balance=Decimal("0"),  # Balance starts at 0, updated by transactions
        )

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        return account

    async def get_account(
        self, user_id: UUID, account_id: UUID
    ) -> Account | None:
        """
        Get account by ID.

        Args:
            user_id: Owner user ID (for access control)
            account_id: Account ID

        Returns:
            Account if found and owned by user, None otherwise
        """
        stmt = select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_accounts(self, user_id: UUID) -> list[Account]:
        """
        List all accounts for a user.

        Args:
            user_id: Owner user ID

        Returns:
            List of user's accounts
        """
        stmt = select(Account).where(Account.user_id == user_id).order_by(Account.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_account(
        self, user_id: UUID, account_id: UUID, data: AccountUpdate
    ) -> Account | None:
        """
        Update an account.

        Args:
            user_id: Owner user ID (for access control)
            account_id: Account ID
            data: Update data

        Returns:
            Updated account if found, None otherwise
        """
        account = await self.get_account(user_id, account_id)
        if not account:
            return None

        if data.name is not None:
            account.name = data.name

        await self.db.commit()
        await self.db.refresh(account)

        return account

    async def delete_account(
        self, user_id: UUID, account_id: UUID
    ) -> bool:
        """
        Delete an account.

        Args:
            user_id: Owner user ID (for access control)
            account_id: Account ID

        Returns:
            True if deleted, False if not found
        """
        account = await self.get_account(user_id, account_id)
        if not account:
            return False

        await self.db.delete(account)
        await self.db.commit()

        return True

    async def update_balance(
        self, account_id: UUID, amount: Decimal
    ) -> None:
        """
        Update account balance by adding amount.

        This is called when transactions are approved.

        Args:
            account_id: Account ID
            amount: Amount to add (can be negative)
        """
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()

        if account:
            account.balance += amount
            await self.db.commit()

    async def update_sync_status(
        self,
        account_id: UUID,
        status: SyncStatus,
        error: str | None = None,
    ) -> None:
        """
        Update account sync status (FR-010a).

        Args:
            account_id: Account ID
            status: New sync status
            error: Error message if status is FAILED
        """
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()

        if account:
            account.sync_status = status
            account.last_sync_at = datetime.now(UTC)
            account.sync_error = error if status == SyncStatus.FAILED else None
            await self.db.commit()

    async def retry_sync(
        self, user_id: UUID, account_id: UUID
    ) -> Account | None:
        """
        Retry sync for an account (FR-010b).

        Resets the sync status to PENDING and clears any previous error.
        For MVP with CSV import, this allows user to upload a new CSV.

        Args:
            user_id: Owner user ID (for access control)
            account_id: Account ID

        Returns:
            Updated account if found, None otherwise
        """
        account = await self.get_account(user_id, account_id)
        if not account:
            return None

        account.sync_status = SyncStatus.PENDING
        account.sync_error = None

        await self.db.commit()
        await self.db.refresh(account)

        return account
