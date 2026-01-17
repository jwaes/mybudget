"""
Unit tests for Transaction model.

Following TDD principles - test written before implementation.
"""
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.user import User


@pytest.mark.unit
class TestTransactionModel:
    """Unit tests for Transaction model."""

    def test_transaction_creation(self) -> None:
        """Test creating a Transaction instance with required fields."""
        from mybudget.models.transaction import Transaction

        transaction = Transaction(
            date=date(2026, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-50.00"),
        )

        assert transaction.date == date(2026, 1, 15)
        assert transaction.payee == "Grocery Store"
        assert transaction.amount == Decimal("-50.00")

    def test_transaction_state_enum_values(self) -> None:
        """Test that TransactionState enum has correct values."""
        from mybudget.models.transaction import TransactionState

        assert TransactionState.INBOX.value == "INBOX"
        assert TransactionState.APPROVED.value == "APPROVED"
        assert TransactionState.CLEARED.value == "CLEARED"

    @pytest.mark.asyncio
    async def test_transaction_default_state_on_insert(
        self, db_session: AsyncSession
    ) -> None:
        """Test that default state is INBOX when inserted to database."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction, TransactionState

        user = User(email="tx_default@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Payee",
            amount=Decimal("-25.00"),
        )

        db_session.add(transaction)
        await db_session.flush()

        assert transaction.state == TransactionState.INBOX

    @pytest.mark.asyncio
    async def test_transaction_timestamps_auto_generated(
        self, db_session: AsyncSession
    ) -> None:
        """Test that created_at and updated_at are auto-generated on insert."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction

        user = User(email="tx_timestamps@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Payee",
            amount=Decimal("-25.00"),
        )

        db_session.add(transaction)
        await db_session.flush()

        assert transaction.created_at is not None
        assert transaction.updated_at is not None
        assert isinstance(transaction.created_at, datetime)
        assert isinstance(transaction.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_transaction_persistence(self, db_session: AsyncSession) -> None:
        """Test that Transaction can be persisted to database."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction, TransactionState

        user = User(email="tx_persist@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Albert Heijn",
            amount=Decimal("-75.50"),
            memo="Weekly groceries",
            state=TransactionState.APPROVED,
        )

        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        # Query the transaction back
        stmt = select(Transaction).where(Transaction.payee == "Albert Heijn")
        result = await db_session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.id == transaction.id
        assert retrieved.user_id == user.id
        assert retrieved.account_id == account.id
        assert retrieved.date == date(2026, 1, 15)
        assert retrieved.payee == "Albert Heijn"
        assert retrieved.amount == Decimal("-75.50")
        assert retrieved.memo == "Weekly groceries"
        assert retrieved.state == TransactionState.APPROVED

    @pytest.mark.asyncio
    async def test_transaction_nullable_category(self, db_session: AsyncSession) -> None:
        """Test that category_id can be null (for INBOX transactions)."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction

        user = User(email="tx_null_cat@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Unknown Payee",
            amount=Decimal("-30.00"),
            category_id=None,
        )

        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.category_id is None

    @pytest.mark.asyncio
    async def test_transaction_nullable_timestamps(self, db_session: AsyncSession) -> None:
        """Test that approved_at and cleared_at are nullable."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction

        user = User(email="tx_null_ts@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Payee",
            amount=Decimal("-25.00"),
        )

        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.approved_at is None
        assert transaction.cleared_at is None

    @pytest.mark.asyncio
    async def test_transaction_user_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting user cascades to transactions."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction

        user = User(email="tx_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test",
            amount=Decimal("-50.00"),
        )
        db_session.add(transaction)
        await db_session.commit()

        tx_id = transaction.id

        await db_session.delete(user)
        await db_session.commit()

        stmt = select(Transaction).where(Transaction.id == tx_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_transaction_account_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting account cascades to transactions."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction

        user = User(email="tx_acc_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Delete Me",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test",
            amount=Decimal("-50.00"),
        )
        db_session.add(transaction)
        await db_session.commit()

        tx_id = transaction.id

        await db_session.delete(account)
        await db_session.commit()

        stmt = select(Transaction).where(Transaction.id == tx_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_transaction_decimal_precision(self, db_session: AsyncSession) -> None:
        """Test that transaction amount maintains DECIMAL(19,4) precision."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.transaction import Transaction

        user = User(email="tx_precision@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        # Use value within DECIMAL(19,4) range (max ~10^15)
        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Precision Test",
            amount=Decimal("-123456789012.1234"),
        )

        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        assert transaction.amount == Decimal("-123456789012.1234")

    def test_transaction_positive_amount_is_income(self) -> None:
        """Test that positive amounts represent income."""
        from mybudget.models.transaction import Transaction

        transaction = Transaction(
            date=date(2026, 1, 15),
            payee="Salary Deposit",
            amount=Decimal("5000.00"),
        )

        assert transaction.amount > 0

    def test_transaction_negative_amount_is_expense(self) -> None:
        """Test that negative amounts represent expenses."""
        from mybudget.models.transaction import Transaction

        transaction = Transaction(
            date=date(2026, 1, 15),
            payee="Restaurant",
            amount=Decimal("-45.00"),
        )

        assert transaction.amount < 0

    def test_transaction_repr(self) -> None:
        """Test that Transaction has readable representation."""
        from mybudget.models.transaction import Transaction

        transaction = Transaction(
            date=date(2026, 1, 15),
            payee="Test Payee",
            amount=Decimal("-100.00"),
        )

        repr_str = repr(transaction)
        assert "Transaction" in repr_str
