"""
Transaction service for business logic operations.
"""
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.account import Account
from mybudget.models.category import Category
from mybudget.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionApprove,
)


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(dt_timezone.utc)


class TransactionService:
    """Service for transaction operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_transaction(
        self, user_id: UUID, data: TransactionCreate
    ) -> Transaction | None:
        """
        Create a new transaction.

        Returns None if the specified account doesn't exist or belong to user.
        """
        # Verify account exists and belongs to user
        account = await self._get_account(user_id, data.account_id)
        if not account:
            return None

        # Verify category if provided
        if data.category_id:
            category = await self._get_category(user_id, data.category_id)
            if not category:
                return None

        transaction = Transaction(
            user_id=user_id,
            account_id=data.account_id,
            category_id=data.category_id,
            date=data.date,
            payee=data.payee,
            amount=data.amount,
            memo=data.memo,
            state=TransactionState.INBOX,
        )

        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def get_transaction(
        self, user_id: UUID, transaction_id: UUID
    ) -> Transaction | None:
        """Get transaction by ID."""
        stmt = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_transactions(
        self,
        user_id: UUID,
        account_id: UUID | None = None,
        state: TransactionState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """
        List transactions for a user with optional filters.

        Returns tuple of (transactions, total_count).
        """
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)

        if state is not None:
            stmt = stmt.where(Transaction.state == state)

        # Get total count
        count_stmt = stmt
        count_result = await self.db.execute(count_stmt)
        total = len(list(count_result.scalars().all()))

        # Add ordering and pagination
        stmt = stmt.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        transactions = list(result.scalars().all())

        return transactions, total

    async def update_transaction(
        self, user_id: UUID, transaction_id: UUID, data: TransactionUpdate
    ) -> Transaction | None:
        """Update a transaction.

        Returns None if transaction not found.
        Raises ValueError if transaction is cleared (locked).
        """
        transaction = await self.get_transaction(user_id, transaction_id)
        if not transaction:
            return None

        # Cleared transactions cannot be modified
        if transaction.state == TransactionState.CLEARED:
            raise ValueError("Cleared transactions cannot be modified")

        if data.date is not None:
            transaction.date = data.date
        if data.payee is not None:
            transaction.payee = data.payee
        if data.amount is not None:
            transaction.amount = data.amount
        if data.memo is not None:
            transaction.memo = data.memo
        if data.category_id is not None:
            # Verify category exists
            category = await self._get_category(user_id, data.category_id)
            if not category:
                return None
            transaction.category_id = data.category_id

        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def approve_transaction(
        self, user_id: UUID, transaction_id: UUID, data: TransactionApprove
    ) -> Transaction | None:
        """
        Approve a transaction, optionally with a category.

        Changes state from INBOX to APPROVED and updates account balance.
        If no category_id is provided, the money goes to "Ready to Assign".
        """
        transaction = await self.get_transaction(user_id, transaction_id)
        if not transaction:
            return None

        if transaction.state != TransactionState.INBOX:
            return transaction  # Already approved

        # Verify category exists if provided
        if data.category_id is not None:
            category = await self._get_category(user_id, data.category_id)
            if not category:
                return None
            transaction.category_id = data.category_id

        # Update transaction state
        transaction.state = TransactionState.APPROVED
        transaction.approved_at = utc_now()

        # Update account balance
        await self._update_account_balance(transaction.account_id, transaction.amount)

        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def unapprove_transaction(
        self, user_id: UUID, transaction_id: UUID
    ) -> Transaction | None:
        """
        Unapprove a transaction.

        Changes state from APPROVED back to INBOX and reverses account balance.
        """
        transaction = await self.get_transaction(user_id, transaction_id)
        if not transaction:
            return None

        if transaction.state != TransactionState.APPROVED:
            return transaction  # Not approved, nothing to do

        # Reverse account balance
        await self._update_account_balance(transaction.account_id, -transaction.amount)

        # Update transaction
        transaction.state = TransactionState.INBOX
        transaction.approved_at = None

        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def delete_transaction(
        self, user_id: UUID, transaction_id: UUID
    ) -> bool:
        """Delete a transaction."""
        transaction = await self.get_transaction(user_id, transaction_id)
        if not transaction:
            return False

        # If approved, reverse the balance first
        if transaction.state == TransactionState.APPROVED:
            await self._update_account_balance(transaction.account_id, -transaction.amount)

        await self.db.delete(transaction)
        await self.db.commit()

        return True

    async def _get_account(self, user_id: UUID, account_id: UUID) -> Account | None:
        """Get account by ID, verifying ownership."""
        stmt = select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_category(self, user_id: UUID, category_id: UUID) -> Category | None:
        """Get category by ID, verifying ownership."""
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_account_balance(self, account_id: UUID, amount: Decimal) -> None:
        """Update account balance by adding amount."""
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()

        if account:
            account.balance += amount
