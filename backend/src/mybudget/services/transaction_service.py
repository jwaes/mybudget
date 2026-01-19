"""
Transaction service for business logic operations.
"""
from datetime import UTC, datetime
from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.account import Account
from mybudget.models.category import Category
from mybudget.models.transaction import CategorizationSource, Transaction, TransactionState
from mybudget.schemas.transaction import (
    TransactionApprove,
    TransactionBulkResult,
    TransactionCreate,
    TransactionUpdate,
)


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


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

        If no category is provided, automatically applies categorization rules
        based on payee matching (sets categorization_source = RULE).

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

        # Apply categorization rules if no category provided
        if transaction.category_id is None:
            from mybudget.services.categorization_rule_service import CategorizationRuleService
            rule_service = CategorizationRuleService(self.db)
            await rule_service.apply_rules_to_transaction(user_id, transaction)

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

    async def search_transactions(
        self,
        user_id: UUID,
        payee_search: str | None = None,
        memo_search: str | None = None,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        category_id: UUID | None = None,
        uncategorized_only: bool = False,
        account_id: UUID | None = None,
        state: TransactionState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """
        Search transactions with multiple filter criteria.

        Args:
            user_id: Owner user ID
            payee_search: Partial match, case-insensitive search on payee (FR-046)
            memo_search: Partial match, case-insensitive search on memo (FR-047)
            date_from: Filter transactions on or after this date (FR-048)
            date_to: Filter transactions on or before this date (FR-048)
            amount_min: Filter transactions with amount >= this value (FR-049)
            amount_max: Filter transactions with amount <= this value (FR-049)
            category_id: Filter by specific category (FR-050)
            uncategorized_only: If True, filter for NULL category_id (FR-050)
            account_id: Filter by account (FR-051)
            state: Filter by transaction state (FR-052)
            limit: Maximum results to return
            offset: Number of results to skip

        Returns:
            Tuple of (transactions, total_count).
        """
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        # FR-046: payee_search - partial match, case-insensitive
        if payee_search is not None:
            stmt = stmt.where(
                func.lower(Transaction.payee).contains(func.lower(payee_search))
            )

        # FR-047: memo_search - partial match, case-insensitive
        if memo_search is not None:
            stmt = stmt.where(
                func.lower(Transaction.memo).contains(func.lower(memo_search))
            )

        # FR-048: date range filter (inclusive)
        if date_from is not None:
            stmt = stmt.where(Transaction.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Transaction.date <= date_to)

        # FR-049: amount range filter (inclusive)
        if amount_min is not None:
            stmt = stmt.where(Transaction.amount >= amount_min)
        if amount_max is not None:
            stmt = stmt.where(Transaction.amount <= amount_max)

        # FR-050: category filter
        if uncategorized_only:
            stmt = stmt.where(Transaction.category_id.is_(None))
        elif category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)

        # FR-051: account filter
        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)

        # FR-052: state filter
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

        # Update transaction state and categorization source
        transaction.state = TransactionState.APPROVED
        transaction.approved_at = utc_now()
        transaction.categorization_source = CategorizationSource.MANUAL

        # Update account balance
        await self._update_account_balance(transaction.account_id, transaction.amount)

        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def batch_approve_transactions(
        self,
        user_id: UUID,
        transaction_ids: list[UUID],
        category_id: UUID,
    ) -> TransactionBulkResult:
        """
        Batch approve multiple transactions with the same category (FR-045).

        Args:
            user_id: Owner user ID
            transaction_ids: List of transaction IDs to approve
            category_id: Category to assign to all transactions

        Returns:
            TransactionBulkResult with success/failure counts
        """
        # Verify category exists
        category = await self._get_category(user_id, category_id)
        if not category:
            return TransactionBulkResult(
                success_count=0,
                failed_count=len(transaction_ids),
                failed_ids=transaction_ids,
            )

        success_count = 0
        failed_ids: list[UUID] = []

        for transaction_id in transaction_ids:
            transaction = await self.get_transaction(user_id, transaction_id)
            if not transaction or transaction.state != TransactionState.INBOX:
                failed_ids.append(transaction_id)
                continue

            # Approve the transaction
            transaction.category_id = category_id
            transaction.state = TransactionState.APPROVED
            transaction.approved_at = utc_now()
            transaction.categorization_source = CategorizationSource.MANUAL

            # Update account balance
            await self._update_account_balance(transaction.account_id, transaction.amount)
            success_count += 1

        await self.db.commit()

        return TransactionBulkResult(
            success_count=success_count,
            failed_count=len(failed_ids),
            failed_ids=failed_ids,
        )

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
