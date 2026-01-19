"""
Unit tests for ReconciliationService.

Tests for reconciliation session management and transaction clearing.
"""
from datetime import date, datetime, UTC
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.account import Account, AccountType
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.reconciliation import Reconciliation, ReconciliationStatus
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.user import User
from mybudget.schemas.reconciliation import (
    ReconciliationCreate,
    ReconciliationCreateAdjustment,
    ReconciliationMarkCleared,
    ReconciliationUnmarkCleared,
)
from mybudget.services.reconciliation_service import ReconciliationService


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email=f"reconcile_test_{uuid4()}@example.com",
        password_hash="hashed",
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def another_user(db_session: AsyncSession) -> User:
    """Create another test user for isolation tests."""
    user = User(
        email=f"another_user_{uuid4()}@example.com",
        password_hash="hashed",
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def account(db_session: AsyncSession, user: User) -> Account:
    """Create a test account."""
    account = Account(
        user_id=user.id,
        name="Test Checking",
        account_type=AccountType.CHECKING,
        initial_balance=Decimal("1000.00"),
        balance=Decimal("500.00"),
    )
    db_session.add(account)
    await db_session.flush()
    return account


@pytest.fixture
async def account2(db_session: AsyncSession, user: User) -> Account:
    """Create a second test account."""
    account = Account(
        user_id=user.id,
        name="Test Savings",
        account_type=AccountType.SAVINGS,
        initial_balance=Decimal("5000.00"),
        balance=Decimal("5000.00"),
    )
    db_session.add(account)
    await db_session.flush()
    return account


@pytest.fixture
async def category(db_session: AsyncSession, user: User) -> Category:
    """Create a test category."""
    group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
    db_session.add(group)
    await db_session.flush()

    category = Category(user_id=user.id, group_id=group.id, name="Adjustments")
    db_session.add(category)
    await db_session.flush()
    return category


@pytest.fixture
async def approved_transactions(
    db_session: AsyncSession,
    user: User,
    account: Account,
) -> list[Transaction]:
    """Create approved transactions for testing."""
    txs = [
        Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Store A",
            amount=Decimal("-100.00"),
            state=TransactionState.APPROVED,
        ),
        Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 12),
            payee="Store B",
            amount=Decimal("-200.00"),
            state=TransactionState.APPROVED,
        ),
        Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Deposit",
            amount=Decimal("500.00"),
            state=TransactionState.APPROVED,
        ),
    ]
    db_session.add_all(txs)
    await db_session.flush()
    return txs


class TestStartReconciliation:
    """Tests for starting a reconciliation session."""

    @pytest.mark.asyncio
    async def test_start_reconciliation_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test successfully starting a reconciliation session."""
        service = ReconciliationService(db_session)
        data = ReconciliationCreate(
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
        )

        result = await service.start_reconciliation(user.id, data)

        assert result is not None
        assert result.user_id == user.id
        assert result.account_id == account.id
        assert result.statement_balance == Decimal("1200.00")
        assert result.statement_date == date(2026, 1, 15)
        assert result.status == ReconciliationStatus.IN_PROGRESS
        assert result.adjustment_transaction_id is None
        assert result.completed_at is None

    @pytest.mark.asyncio
    async def test_start_reconciliation_nonexistent_account(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test starting reconciliation with nonexistent account returns None."""
        service = ReconciliationService(db_session)
        data = ReconciliationCreate(
            account_id=uuid4(),
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
        )

        result = await service.start_reconciliation(user.id, data)

        assert result is None

    @pytest.mark.asyncio
    async def test_start_reconciliation_other_user_account(
        self, db_session: AsyncSession, user: User, another_user: User, account: Account
    ) -> None:
        """Test starting reconciliation with another user's account returns None."""
        service = ReconciliationService(db_session)
        data = ReconciliationCreate(
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
        )

        result = await service.start_reconciliation(another_user.id, data)

        assert result is None


class TestGetReconciliation:
    """Tests for getting a reconciliation session."""

    @pytest.mark.asyncio
    async def test_get_reconciliation_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test getting an existing reconciliation."""
        # Create a reconciliation first
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.get_reconciliation(user.id, reconciliation.id)

        assert result is not None
        assert result.id == reconciliation.id
        assert result.statement_balance == Decimal("1200.00")

    @pytest.mark.asyncio
    async def test_get_reconciliation_not_found(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test getting a nonexistent reconciliation returns None."""
        service = ReconciliationService(db_session)
        result = await service.get_reconciliation(user.id, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_reconciliation_other_user(
        self, db_session: AsyncSession, user: User, another_user: User, account: Account
    ) -> None:
        """Test getting another user's reconciliation returns None."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.get_reconciliation(another_user.id, reconciliation.id)

        assert result is None


class TestListReconciliations:
    """Tests for listing reconciliation sessions."""

    @pytest.mark.asyncio
    async def test_list_reconciliations_all(
        self, db_session: AsyncSession, user: User, account: Account, account2: Account
    ) -> None:
        """Test listing all reconciliations for a user."""
        recon1 = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        recon2 = Reconciliation(
            user_id=user.id,
            account_id=account2.id,
            statement_balance=Decimal("5500.00"),
            statement_date=date(2026, 1, 14),
            status=ReconciliationStatus.COMPLETED,
        )
        db_session.add_all([recon1, recon2])
        await db_session.flush()

        service = ReconciliationService(db_session)
        results = await service.list_reconciliations(user.id)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_reconciliations_by_account(
        self, db_session: AsyncSession, user: User, account: Account, account2: Account
    ) -> None:
        """Test listing reconciliations filtered by account."""
        recon1 = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        recon2 = Reconciliation(
            user_id=user.id,
            account_id=account2.id,
            statement_balance=Decimal("5500.00"),
            statement_date=date(2026, 1, 14),
            status=ReconciliationStatus.COMPLETED,
        )
        db_session.add_all([recon1, recon2])
        await db_session.flush()

        service = ReconciliationService(db_session)
        results = await service.list_reconciliations(user.id, account_id=account.id)

        assert len(results) == 1
        assert results[0].account_id == account.id

    @pytest.mark.asyncio
    async def test_list_reconciliations_user_isolation(
        self, db_session: AsyncSession, user: User, another_user: User, account: Account
    ) -> None:
        """Test that listing only returns own reconciliations."""
        recon = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(recon)
        await db_session.flush()

        service = ReconciliationService(db_session)
        results = await service.list_reconciliations(another_user.id)

        assert len(results) == 0


class TestMarkTransactionsCleared:
    """Tests for marking transactions as cleared."""

    @pytest.mark.asyncio
    async def test_mark_transactions_cleared_success(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        approved_transactions: list[Transaction],
    ) -> None:
        """Test marking transactions as cleared."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationMarkCleared(
            transaction_ids=[approved_transactions[0].id, approved_transactions[1].id]
        )
        result = await service.mark_transactions_cleared(user.id, reconciliation.id, data)

        assert result is not None
        # Verify transactions are cleared
        await db_session.refresh(approved_transactions[0])
        await db_session.refresh(approved_transactions[1])
        assert approved_transactions[0].state == TransactionState.CLEARED
        assert approved_transactions[1].state == TransactionState.CLEARED
        assert approved_transactions[0].cleared_at is not None
        assert approved_transactions[1].cleared_at is not None

    @pytest.mark.asyncio
    async def test_mark_transactions_cleared_nonexistent_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
        approved_transactions: list[Transaction],
    ) -> None:
        """Test marking cleared for nonexistent reconciliation returns None."""
        service = ReconciliationService(db_session)
        data = ReconciliationMarkCleared(
            transaction_ids=[approved_transactions[0].id]
        )
        result = await service.mark_transactions_cleared(user.id, uuid4(), data)

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_transactions_cleared_nonexistent_transaction(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test marking nonexistent transaction returns None."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationMarkCleared(transaction_ids=[uuid4()])
        result = await service.mark_transactions_cleared(user.id, reconciliation.id, data)

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_transactions_cleared_wrong_account(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        account2: Account,
    ) -> None:
        """Test marking transaction from different account returns None."""
        # Create transaction on account2
        tx = Transaction(
            user_id=user.id,
            account_id=account2.id,
            date=date(2026, 1, 10),
            payee="Store",
            amount=Decimal("-100.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx)

        # Create reconciliation on account1
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationMarkCleared(transaction_ids=[tx.id])
        result = await service.mark_transactions_cleared(user.id, reconciliation.id, data)

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_transactions_cleared_completed_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        approved_transactions: list[Transaction],
    ) -> None:
        """Test cannot mark cleared on completed reconciliation."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.COMPLETED,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationMarkCleared(transaction_ids=[approved_transactions[0].id])
        result = await service.mark_transactions_cleared(user.id, reconciliation.id, data)

        # Returns reconciliation but doesn't modify
        assert result is not None
        await db_session.refresh(approved_transactions[0])
        assert approved_transactions[0].state == TransactionState.APPROVED


class TestUnmarkTransactionsCleared:
    """Tests for unmarking transactions as cleared."""

    @pytest.mark.asyncio
    async def test_unmark_transactions_cleared_success(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test unmarking transactions as cleared."""
        # Create cleared transaction
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Store",
            amount=Decimal("-100.00"),
            state=TransactionState.CLEARED,
            cleared_at=datetime.now(UTC),
        )
        db_session.add(tx)

        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationUnmarkCleared(transaction_ids=[tx.id])
        result = await service.unmark_transactions_cleared(user.id, reconciliation.id, data)

        assert result is not None
        await db_session.refresh(tx)
        assert tx.state == TransactionState.APPROVED
        assert tx.cleared_at is None

    @pytest.mark.asyncio
    async def test_unmark_transactions_cleared_nonexistent_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test unmarking for nonexistent reconciliation returns None."""
        service = ReconciliationService(db_session)
        data = ReconciliationUnmarkCleared(transaction_ids=[uuid4()])
        result = await service.unmark_transactions_cleared(user.id, uuid4(), data)

        assert result is None

    @pytest.mark.asyncio
    async def test_unmark_transactions_cleared_completed_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test cannot unmark on completed reconciliation."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Store",
            amount=Decimal("-100.00"),
            state=TransactionState.CLEARED,
            cleared_at=datetime.now(UTC),
        )
        db_session.add(tx)

        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.COMPLETED,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationUnmarkCleared(transaction_ids=[tx.id])
        result = await service.unmark_transactions_cleared(user.id, reconciliation.id, data)

        # Returns reconciliation but doesn't modify
        assert result is not None
        await db_session.refresh(tx)
        assert tx.state == TransactionState.CLEARED


class TestCreateAdjustment:
    """Tests for creating adjustment transactions."""

    @pytest.mark.asyncio
    async def test_create_adjustment_success(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        category: Category,
    ) -> None:
        """Test creating an adjustment transaction."""
        # Create a cleared transaction
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Store",
            amount=Decimal("-100.00"),
            state=TransactionState.CLEARED,
            cleared_at=datetime.now(UTC),
        )
        db_session.add(tx)

        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("950.00"),  # Expects 1000 - 100 + 50 adjustment
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationCreateAdjustment(category_id=category.id)
        recon_result, adj_result = await service.create_adjustment(
            user.id, reconciliation.id, data
        )

        assert recon_result is not None
        assert adj_result is not None
        assert adj_result.payee == "Reconciliation Adjustment"
        assert adj_result.amount == Decimal("50.00")  # 950 - 900 = 50
        assert adj_result.state == TransactionState.CLEARED
        assert adj_result.category_id == category.id

    @pytest.mark.asyncio
    async def test_create_adjustment_nonexistent_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
        category: Category,
    ) -> None:
        """Test creating adjustment for nonexistent reconciliation returns None."""
        service = ReconciliationService(db_session)
        data = ReconciliationCreateAdjustment(category_id=category.id)
        recon_result, adj_result = await service.create_adjustment(
            user.id, uuid4(), data
        )

        assert recon_result is None
        assert adj_result is None

    @pytest.mark.asyncio
    async def test_create_adjustment_nonexistent_category(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test creating adjustment with nonexistent category returns None."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationCreateAdjustment(category_id=uuid4())
        recon_result, adj_result = await service.create_adjustment(
            user.id, reconciliation.id, data
        )

        assert recon_result is None
        assert adj_result is None

    @pytest.mark.asyncio
    async def test_create_adjustment_no_discrepancy(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        category: Category,
    ) -> None:
        """Test creating adjustment when no discrepancy exists returns None."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1000.00"),  # Matches initial balance
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationCreateAdjustment(category_id=category.id)
        recon_result, adj_result = await service.create_adjustment(
            user.id, reconciliation.id, data
        )

        assert recon_result is None
        assert adj_result is None

    @pytest.mark.asyncio
    async def test_create_adjustment_completed_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        category: Category,
    ) -> None:
        """Test cannot create adjustment on completed reconciliation."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.COMPLETED,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        data = ReconciliationCreateAdjustment(category_id=category.id)
        recon_result, adj_result = await service.create_adjustment(
            user.id, reconciliation.id, data
        )

        assert recon_result is None
        assert adj_result is None


class TestCompleteReconciliation:
    """Tests for completing a reconciliation session."""

    @pytest.mark.asyncio
    async def test_complete_reconciliation_success(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test completing a reconciliation when balanced."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1000.00"),  # Matches initial balance
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.complete_reconciliation(user.id, reconciliation.id)

        assert result is not None
        assert result.status == ReconciliationStatus.COMPLETED
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_reconciliation_with_discrepancy(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test cannot complete reconciliation with discrepancy."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),  # Doesn't match
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.complete_reconciliation(user.id, reconciliation.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_reconciliation_nonexistent(
        self,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test completing nonexistent reconciliation returns None."""
        service = ReconciliationService(db_session)
        result = await service.complete_reconciliation(user.id, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_complete_reconciliation_already_completed(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test completing already completed reconciliation returns it."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1000.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.COMPLETED,
            completed_at=datetime.now(UTC),
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.complete_reconciliation(user.id, reconciliation.id)

        assert result is not None
        assert result.status == ReconciliationStatus.COMPLETED


class TestCancelReconciliation:
    """Tests for cancelling a reconciliation session."""

    @pytest.mark.asyncio
    async def test_cancel_reconciliation_success(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test cancelling an in-progress reconciliation."""
        # Create cleared transaction
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Store",
            amount=Decimal("-100.00"),
            state=TransactionState.CLEARED,
            cleared_at=datetime.now(UTC),
        )
        db_session.add(tx)

        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.cancel_reconciliation(user.id, reconciliation.id)

        assert result is True
        # Verify transaction is back to approved
        await db_session.refresh(tx)
        assert tx.state == TransactionState.APPROVED
        assert tx.cleared_at is None

    @pytest.mark.asyncio
    async def test_cancel_reconciliation_nonexistent(
        self,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test cancelling nonexistent reconciliation returns False."""
        service = ReconciliationService(db_session)
        result = await service.cancel_reconciliation(user.id, uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_reconciliation_completed(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test cannot cancel completed reconciliation."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1000.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.COMPLETED,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.cancel_reconciliation(user.id, reconciliation.id)

        assert result is False


class TestCalculateClearedBalance:
    """Tests for calculating cleared balance."""

    @pytest.mark.asyncio
    async def test_calculate_cleared_balance_with_transactions(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test calculating cleared balance with cleared transactions."""
        # Create cleared transactions
        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Store A",
            amount=Decimal("-100.00"),
            state=TransactionState.CLEARED,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 12),
            payee="Deposit",
            amount=Decimal("500.00"),
            state=TransactionState.CLEARED,
        )
        db_session.add_all([tx1, tx2])

        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1400.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.calculate_cleared_balance(reconciliation)

        # initial_balance (1000) + (-100) + (500) = 1400
        assert result == Decimal("1400.00")

    @pytest.mark.asyncio
    async def test_calculate_cleared_balance_no_transactions(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
    ) -> None:
        """Test calculating cleared balance with no cleared transactions."""
        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1000.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        result = await service.calculate_cleared_balance(reconciliation)

        # Just initial balance
        assert result == Decimal("1000.00")


class TestGetTransactionsForReconciliation:
    """Tests for getting transactions for a reconciliation."""

    @pytest.mark.asyncio
    async def test_get_transactions_for_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        approved_transactions: list[Transaction],
    ) -> None:
        """Test getting transactions with cleared status."""
        # Mark one as cleared
        approved_transactions[0].state = TransactionState.CLEARED
        approved_transactions[0].cleared_at = datetime.now(UTC)

        reconciliation = Reconciliation(
            user_id=user.id,
            account_id=account.id,
            statement_balance=Decimal("1200.00"),
            statement_date=date(2026, 1, 15),
            status=ReconciliationStatus.IN_PROGRESS,
        )
        db_session.add(reconciliation)
        await db_session.flush()

        service = ReconciliationService(db_session)
        results = await service.get_transactions_for_reconciliation(
            user.id, reconciliation.id
        )

        assert len(results) == 3
        # Find the cleared one
        cleared_items = [(tx, is_cleared) for tx, is_cleared in results if is_cleared]
        assert len(cleared_items) == 1
        assert cleared_items[0][0].id == approved_transactions[0].id

    @pytest.mark.asyncio
    async def test_get_transactions_for_nonexistent_reconciliation(
        self,
        db_session: AsyncSession,
        user: User,
    ) -> None:
        """Test getting transactions for nonexistent reconciliation."""
        service = ReconciliationService(db_session)
        results = await service.get_transactions_for_reconciliation(user.id, uuid4())

        assert results == []
