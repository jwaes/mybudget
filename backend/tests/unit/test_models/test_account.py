"""
Unit tests for Account model.

Following TDD principles - test written before implementation.
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.user import User


@pytest.mark.unit
class TestAccountModel:
    """Unit tests for Account model."""

    def test_account_creation(self) -> None:
        """Test creating an Account instance with required fields."""
        from mybudget.models.account import Account, AccountType

        account = Account(
            name="ING Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )

        assert account.name == "ING Checking"
        assert account.account_type == AccountType.CHECKING
        assert account.initial_balance == Decimal("1000.00")

    def test_account_type_enum_values(self) -> None:
        """Test that AccountType enum has correct values."""
        from mybudget.models.account import AccountType

        assert AccountType.CHECKING.value == "CHECKING"
        assert AccountType.SAVINGS.value == "SAVINGS"

    @pytest.mark.asyncio
    async def test_account_default_balance_on_insert(
        self, db_session: AsyncSession
    ) -> None:
        """Test that default balance is 0 when inserted to database."""
        from mybudget.models.account import Account, AccountType

        # First create a user (required foreign key)
        user = User(email="account_test@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("500.00"),
        )

        db_session.add(account)
        await db_session.flush()

        assert account.balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_account_timestamps_auto_generated_on_insert(
        self, db_session: AsyncSession
    ) -> None:
        """Test that created_at and updated_at are auto-generated on insert."""
        from mybudget.models.account import Account, AccountType

        user = User(email="timestamps_account@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Timestamps Test",
            account_type=AccountType.SAVINGS,
            initial_balance=Decimal("0"),
        )

        db_session.add(account)
        await db_session.flush()

        assert account.created_at is not None
        assert account.updated_at is not None
        assert isinstance(account.created_at, datetime)
        assert isinstance(account.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_account_persistence(self, db_session: AsyncSession) -> None:
        """Test that Account can be persisted to database."""
        from mybudget.models.account import Account, AccountType

        user = User(email="persist_account@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="KBC Savings",
            account_type=AccountType.SAVINGS,
            initial_balance=Decimal("2500.5000"),
            balance=Decimal("2600.0000"),
        )

        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        # Query the account back
        stmt = select(Account).where(Account.name == "KBC Savings")
        result = await db_session.execute(stmt)
        retrieved_account = result.scalar_one()

        assert retrieved_account.id == account.id
        assert retrieved_account.user_id == user.id
        assert retrieved_account.name == "KBC Savings"
        assert retrieved_account.account_type == AccountType.SAVINGS
        assert retrieved_account.initial_balance == Decimal("2500.5000")
        assert retrieved_account.balance == Decimal("2600.0000")

    @pytest.mark.asyncio
    async def test_account_user_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting user cascades to accounts."""
        from mybudget.models.account import Account, AccountType

        user = User(email="cascade_delete@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Cascade Test",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("100.00"),
        )
        db_session.add(account)
        await db_session.commit()

        account_id = account.id

        # Delete the user
        await db_session.delete(user)
        await db_session.commit()

        # Account should be gone
        stmt = select(Account).where(Account.id == account_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_account_decimal_precision(self, db_session: AsyncSession) -> None:
        """Test that account balance maintains DECIMAL(19,4) precision."""
        from mybudget.models.account import Account, AccountType

        user = User(email="precision@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        # Use precise decimal values within DECIMAL(19,4) range (max ~10^15)
        account = Account(
            user_id=user.id,
            name="Precision Test",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("123456789012.1234"),
            balance=Decimal("987654321098.9876"),
        )

        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        # Verify precision maintained
        assert account.initial_balance == Decimal("123456789012.1234")
        assert account.balance == Decimal("987654321098.9876")

    def test_account_repr(self) -> None:
        """Test that Account has readable representation."""
        from mybudget.models.account import Account, AccountType

        account = Account(
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("100.00"),
        )

        repr_str = repr(account)
        assert "Account" in repr_str
        assert "Test Account" in repr_str
