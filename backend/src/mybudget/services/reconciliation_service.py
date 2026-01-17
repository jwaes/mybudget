"""
Reconciliation service for business logic operations.
"""
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.account import Account
from mybudget.models.category import Category
from mybudget.models.reconciliation import Reconciliation, ReconciliationStatus
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.schemas.reconciliation import (
    ReconciliationCreate,
    ReconciliationCreateAdjustment,
    ReconciliationMarkCleared,
    ReconciliationUnmarkCleared,
)


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class ReconciliationService:
    """Service for reconciliation operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def start_reconciliation(
        self, user_id: UUID, data: ReconciliationCreate
    ) -> Reconciliation | None:
        """
        Start a new reconciliation session.

        Returns None if the specified account doesn't exist or belong to user.
        """
        # Verify account exists and belongs to user
        account = await self._get_account(user_id, data.account_id)
        if not account:
            return None

        reconciliation = Reconciliation(
            user_id=user_id,
            account_id=data.account_id,
            statement_balance=data.statement_balance,
            statement_date=data.statement_date,
            status=ReconciliationStatus.IN_PROGRESS,
        )

        self.db.add(reconciliation)
        await self.db.commit()
        await self.db.refresh(reconciliation)

        return reconciliation

    async def get_reconciliation(
        self, user_id: UUID, reconciliation_id: UUID
    ) -> Reconciliation | None:
        """Get reconciliation by ID."""
        stmt = select(Reconciliation).where(
            Reconciliation.id == reconciliation_id,
            Reconciliation.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_reconciliations(
        self,
        user_id: UUID,
        account_id: UUID | None = None,
    ) -> list[Reconciliation]:
        """
        List reconciliations for a user with optional account filter.
        """
        stmt = select(Reconciliation).where(Reconciliation.user_id == user_id)

        if account_id is not None:
            stmt = stmt.where(Reconciliation.account_id == account_id)

        stmt = stmt.order_by(Reconciliation.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_transactions_cleared(
        self, user_id: UUID, reconciliation_id: UUID, data: ReconciliationMarkCleared
    ) -> Reconciliation | None:
        """
        Mark transactions as cleared for this reconciliation.

        Returns None if reconciliation not found or any transaction not found.
        """
        reconciliation = await self.get_reconciliation(user_id, reconciliation_id)
        if not reconciliation:
            return None

        if reconciliation.status != ReconciliationStatus.IN_PROGRESS:
            return reconciliation  # Can't modify completed reconciliation

        # Mark each transaction as cleared
        for tx_id in data.transaction_ids:
            transaction = await self._get_transaction(user_id, tx_id)
            if not transaction:
                return None  # Transaction not found
            if transaction.account_id != reconciliation.account_id:
                return None  # Transaction belongs to different account

            transaction.state = TransactionState.CLEARED
            transaction.cleared_at = utc_now()

        await self.db.commit()
        await self.db.refresh(reconciliation)

        return reconciliation

    async def unmark_transactions_cleared(
        self, user_id: UUID, reconciliation_id: UUID, data: ReconciliationUnmarkCleared
    ) -> Reconciliation | None:
        """
        Unmark transactions as cleared.

        Returns None if reconciliation not found or any transaction not found.
        """
        reconciliation = await self.get_reconciliation(user_id, reconciliation_id)
        if not reconciliation:
            return None

        if reconciliation.status != ReconciliationStatus.IN_PROGRESS:
            return reconciliation  # Can't modify completed reconciliation

        # Unmark each transaction
        for tx_id in data.transaction_ids:
            transaction = await self._get_transaction(user_id, tx_id)
            if not transaction:
                return None  # Transaction not found

            if transaction.state == TransactionState.CLEARED:
                transaction.state = TransactionState.APPROVED
                transaction.cleared_at = None

        await self.db.commit()
        await self.db.refresh(reconciliation)

        return reconciliation

    async def create_adjustment(
        self, user_id: UUID, reconciliation_id: UUID, data: ReconciliationCreateAdjustment
    ) -> tuple[Reconciliation, Transaction] | tuple[None, None]:
        """
        Create an adjustment transaction to balance the reconciliation.

        Returns tuple of (reconciliation, adjustment_transaction) or (None, None) if:
        - Reconciliation not found
        - Category not found
        - No discrepancy exists
        """
        reconciliation = await self.get_reconciliation(user_id, reconciliation_id)
        if not reconciliation:
            return None, None

        if reconciliation.status != ReconciliationStatus.IN_PROGRESS:
            return None, None

        # Verify category exists
        category = await self._get_category(user_id, data.category_id)
        if not category:
            return None, None

        # Calculate discrepancy
        cleared_balance = await self.calculate_cleared_balance(reconciliation)
        discrepancy = reconciliation.statement_balance - cleared_balance

        if discrepancy == Decimal("0"):
            return None, None  # No adjustment needed

        # Create adjustment transaction
        adjustment = Transaction(
            user_id=user_id,
            account_id=reconciliation.account_id,
            category_id=data.category_id,
            date=reconciliation.statement_date,
            payee="Reconciliation Adjustment",
            amount=discrepancy,
            memo="Reconciliation Adjustment",
            state=TransactionState.CLEARED,
            cleared_at=utc_now(),
            approved_at=utc_now(),
        )

        self.db.add(adjustment)
        await self.db.flush()

        # Update account balance
        await self._update_account_balance(reconciliation.account_id, discrepancy)

        # Link to reconciliation
        reconciliation.adjustment_transaction_id = adjustment.id

        await self.db.commit()
        await self.db.refresh(reconciliation)
        await self.db.refresh(adjustment)

        return reconciliation, adjustment

    async def complete_reconciliation(
        self, user_id: UUID, reconciliation_id: UUID
    ) -> Reconciliation | None:
        """
        Complete a reconciliation session.

        Returns None if:
        - Reconciliation not found
        - There's a discrepancy (need to create adjustment first)
        """
        reconciliation = await self.get_reconciliation(user_id, reconciliation_id)
        if not reconciliation:
            return None

        if reconciliation.status != ReconciliationStatus.IN_PROGRESS:
            return reconciliation  # Already completed

        # Check for discrepancy
        cleared_balance = await self.calculate_cleared_balance(reconciliation)
        discrepancy = reconciliation.statement_balance - cleared_balance

        if discrepancy != Decimal("0"):
            return None  # Can't complete with discrepancy

        reconciliation.status = ReconciliationStatus.COMPLETED
        reconciliation.completed_at = utc_now()

        await self.db.commit()
        await self.db.refresh(reconciliation)

        return reconciliation

    async def cancel_reconciliation(
        self, user_id: UUID, reconciliation_id: UUID
    ) -> bool:
        """
        Cancel an in-progress reconciliation.

        Unmarks all cleared transactions and deletes the reconciliation.
        """
        reconciliation = await self.get_reconciliation(user_id, reconciliation_id)
        if not reconciliation:
            return False

        if reconciliation.status == ReconciliationStatus.COMPLETED:
            return False  # Can't cancel completed reconciliation

        # Get all cleared transactions for this account
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.account_id == reconciliation.account_id,
            Transaction.state == TransactionState.CLEARED,
        )
        result = await self.db.execute(stmt)
        cleared_transactions = list(result.scalars().all())

        # Unmark them (back to approved)
        for tx in cleared_transactions:
            tx.state = TransactionState.APPROVED
            tx.cleared_at = None

        await self.db.delete(reconciliation)
        await self.db.commit()

        return True

    async def calculate_cleared_balance(
        self, reconciliation: Reconciliation
    ) -> Decimal:
        """
        Calculate the cleared balance for a reconciliation.

        Cleared balance = account's initial balance + sum of cleared transactions.
        """
        # Get account initial balance
        account = await self._get_account_by_id(reconciliation.account_id)
        if not account:
            return Decimal("0")

        # Sum cleared transactions for this account
        stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            Transaction.account_id == reconciliation.account_id,
            Transaction.state == TransactionState.CLEARED,
        )
        result = await self.db.execute(stmt)
        cleared_sum = result.scalar() or Decimal("0")

        return account.initial_balance + cleared_sum

    async def get_transactions_for_reconciliation(
        self, user_id: UUID, reconciliation_id: UUID
    ) -> list[tuple[Transaction, bool]]:
        """
        Get all approved/cleared transactions for a reconciliation's account.

        Returns list of (transaction, is_cleared) tuples.
        """
        reconciliation = await self.get_reconciliation(user_id, reconciliation_id)
        if not reconciliation:
            return []

        # Get all approved or cleared transactions for the account
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.account_id == reconciliation.account_id,
            Transaction.state.in_([TransactionState.APPROVED, TransactionState.CLEARED]),
        ).order_by(Transaction.date.desc())

        result = await self.db.execute(stmt)
        transactions = list(result.scalars().all())

        return [
            (tx, tx.state == TransactionState.CLEARED)
            for tx in transactions
        ]

    async def _get_account(self, user_id: UUID, account_id: UUID) -> Account | None:
        """Get account by ID, verifying ownership."""
        stmt = select(Account).where(
            Account.id == account_id,
            Account.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_account_by_id(self, account_id: UUID) -> Account | None:
        """Get account by ID without ownership check."""
        stmt = select(Account).where(Account.id == account_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_transaction(self, user_id: UUID, transaction_id: UUID) -> Transaction | None:
        """Get transaction by ID, verifying ownership."""
        stmt = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
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
        account = await self._get_account_by_id(account_id)
        if account:
            account.balance += amount
