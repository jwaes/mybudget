"""
Unit tests for TransactionService.

Tests for transaction CRUD operations and search/filter functionality (FR-046 to FR-052).
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.account import Account, AccountType
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.transaction import CategorizationSource, Transaction, TransactionState
from mybudget.models.user import User
from mybudget.schemas.transaction import TransactionApprove, TransactionCreate, TransactionUpdate
from mybudget.services.transaction_service import TransactionService


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email=f"search_test_{uuid4()}@example.com",
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
        balance=Decimal("0"),
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
        balance=Decimal("0"),
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

    category = Category(user_id=user.id, group_id=group.id, name="Groceries")
    db_session.add(category)
    await db_session.flush()
    return category


@pytest.fixture
async def category2(db_session: AsyncSession, user: User, category: Category) -> Category:
    """Create a second test category (uses same group)."""
    # Get the group from the first category
    cat2 = Category(user_id=user.id, group_id=category.group_id, name="Utilities")
    db_session.add(cat2)
    await db_session.flush()
    return cat2


@pytest.fixture
async def transactions(
    db_session: AsyncSession,
    user: User,
    account: Account,
    account2: Account,
    category: Category,
    category2: Category,
) -> list[Transaction]:
    """Create a variety of test transactions for search/filter testing."""
    txs = [
        # Transaction 1: Grocery store, categorized, approved
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2026, 1, 10),
            payee="Whole Foods Market",
            amount=Decimal("-85.50"),
            memo="Weekly groceries",
            state=TransactionState.APPROVED,
        ),
        # Transaction 2: Another grocery, inbox
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=None,
            date=date(2026, 1, 12),
            payee="Trader Joe's",
            amount=Decimal("-42.00"),
            memo="Snacks and wine",
            state=TransactionState.INBOX,
        ),
        # Transaction 3: Utility bill, different category
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category2.id,
            date=date(2026, 1, 15),
            payee="Electric Company",
            amount=Decimal("-125.00"),
            memo="January electric bill",
            state=TransactionState.APPROVED,
        ),
        # Transaction 4: Income, positive amount
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=None,
            date=date(2026, 1, 1),
            payee="Employer Inc",
            amount=Decimal("3500.00"),
            memo="Salary deposit",
            state=TransactionState.APPROVED,
        ),
        # Transaction 5: Different account
        Transaction(
            user_id=user.id,
            account_id=account2.id,
            category_id=None,
            date=date(2026, 1, 5),
            payee="Transfer",
            amount=Decimal("500.00"),
            memo="Savings transfer",
            state=TransactionState.APPROVED,
        ),
        # Transaction 6: Large expense
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=None,
            date=date(2026, 1, 20),
            payee="Best Buy",
            amount=Decimal("-899.99"),
            memo="New laptop",
            state=TransactionState.INBOX,
        ),
        # Transaction 7: Cleared transaction
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2025, 12, 28),
            payee="Old Transaction",
            amount=Decimal("-50.00"),
            memo="December purchase",
            state=TransactionState.CLEARED,
        ),
    ]
    db_session.add_all(txs)
    await db_session.flush()
    return txs


class TestTransactionSearchByPayee:
    """Tests for FR-046: Search by payee (partial match, case-insensitive)."""

    @pytest.mark.asyncio
    async def test_search_payee_exact_match(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test search finds exact payee match."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="Whole Foods Market",
        )

        assert total == 1
        assert results[0].payee == "Whole Foods Market"

    @pytest.mark.asyncio
    async def test_search_payee_partial_match(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test search finds partial payee match."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="Foods",
        )

        assert total == 1
        assert "Foods" in results[0].payee

    @pytest.mark.asyncio
    async def test_search_payee_case_insensitive(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test search is case-insensitive."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="whole foods",
        )

        assert total == 1
        assert results[0].payee == "Whole Foods Market"

    @pytest.mark.asyncio
    async def test_search_payee_multiple_matches(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test search finds multiple matches with common term."""
        service = TransactionService(db_session)
        # Search for stores ending in 's
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="'s",  # Matches "Trader Joe's"
        )

        assert total >= 1

    @pytest.mark.asyncio
    async def test_search_payee_no_match(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test search returns empty for no match."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="NonExistentStore",
        )

        assert total == 0
        assert results == []


class TestTransactionSearchByMemo:
    """Tests for FR-047: Search by memo (partial match, case-insensitive)."""

    @pytest.mark.asyncio
    async def test_search_memo_partial_match(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test search finds partial memo match."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            memo_search="groceries",
        )

        assert total == 1
        assert "groceries" in results[0].memo.lower()

    @pytest.mark.asyncio
    async def test_search_memo_case_insensitive(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test memo search is case-insensitive."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            memo_search="SALARY",
        )

        assert total == 1
        assert "Salary" in results[0].memo

    @pytest.mark.asyncio
    async def test_search_combined_payee_and_memo(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test combined payee and memo search (AND logic)."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="Electric",
            memo_search="bill",
        )

        assert total == 1
        assert results[0].payee == "Electric Company"
        assert "bill" in results[0].memo.lower()


class TestTransactionFilterByDateRange:
    """Tests for FR-048: Filter by date range."""

    @pytest.mark.asyncio
    async def test_filter_date_range(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter by date range returns transactions within range."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            date_from=date(2026, 1, 10),
            date_to=date(2026, 1, 15),
        )

        # Should include transactions on 10th, 12th, and 15th
        assert total == 3
        for tx in results:
            assert date(2026, 1, 10) <= tx.date <= date(2026, 1, 15)

    @pytest.mark.asyncio
    async def test_filter_date_from_only(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter with only date_from (no upper bound)."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            date_from=date(2026, 1, 15),
        )

        for tx in results:
            assert tx.date >= date(2026, 1, 15)

    @pytest.mark.asyncio
    async def test_filter_date_to_only(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter with only date_to (no lower bound)."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            date_to=date(2026, 1, 5),
        )

        for tx in results:
            assert tx.date <= date(2026, 1, 5)


class TestTransactionFilterByAmountRange:
    """Tests for FR-049: Filter by amount range."""

    @pytest.mark.asyncio
    async def test_filter_amount_range(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter by amount range."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            amount_min=Decimal("-100.00"),
            amount_max=Decimal("-40.00"),
        )

        for tx in results:
            assert Decimal("-100.00") <= tx.amount <= Decimal("-40.00")

    @pytest.mark.asyncio
    async def test_filter_amount_min_only(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter with only minimum amount."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            amount_min=Decimal("0"),  # Only positive (income)
        )

        for tx in results:
            assert tx.amount >= Decimal("0")

    @pytest.mark.asyncio
    async def test_filter_large_expenses(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter for large expenses (amount <= -500)."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            amount_max=Decimal("-500.00"),
        )

        for tx in results:
            assert tx.amount <= Decimal("-500.00")


class TestTransactionFilterByCategory:
    """Tests for FR-050: Filter by category (including uncategorized)."""

    @pytest.mark.asyncio
    async def test_filter_by_category(
        self,
        db_session: AsyncSession,
        user: User,
        transactions: list[Transaction],
        category: Category,
    ) -> None:
        """Test filter by specific category."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            category_id=category.id,
        )

        for tx in results:
            assert tx.category_id == category.id

    @pytest.mark.asyncio
    async def test_filter_uncategorized(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter for uncategorized transactions (category_id is None)."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            uncategorized_only=True,
        )

        for tx in results:
            assert tx.category_id is None


class TestTransactionFilterByAccount:
    """Tests for FR-051: Filter by account."""

    @pytest.mark.asyncio
    async def test_filter_by_account(
        self,
        db_session: AsyncSession,
        user: User,
        transactions: list[Transaction],
        account2: Account,
    ) -> None:
        """Test filter by specific account."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            account_id=account2.id,
        )

        assert total == 1  # Only one transaction in account2
        for tx in results:
            assert tx.account_id == account2.id


class TestTransactionFilterByStatus:
    """Tests for FR-052: Filter by status (INBOX, APPROVED, CLEARED)."""

    @pytest.mark.asyncio
    async def test_filter_by_inbox_status(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter for INBOX transactions."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            state=TransactionState.INBOX,
        )

        for tx in results:
            assert tx.state == TransactionState.INBOX

    @pytest.mark.asyncio
    async def test_filter_by_approved_status(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter for APPROVED transactions."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            state=TransactionState.APPROVED,
        )

        for tx in results:
            assert tx.state == TransactionState.APPROVED

    @pytest.mark.asyncio
    async def test_filter_by_cleared_status(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filter for CLEARED transactions."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            state=TransactionState.CLEARED,
        )

        assert total == 1  # Only one cleared transaction
        for tx in results:
            assert tx.state == TransactionState.CLEARED


class TestTransactionCombinedFilters:
    """Tests for combining multiple search and filter criteria."""

    @pytest.mark.asyncio
    async def test_combined_search_and_filters(
        self,
        db_session: AsyncSession,
        user: User,
        transactions: list[Transaction],
        account: Account,
        category: Category,
    ) -> None:
        """Test combining search with multiple filters."""
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="Foods",
            account_id=account.id,
            state=TransactionState.APPROVED,
            category_id=category.id,
        )

        assert total == 1
        tx = results[0]
        assert "Foods" in tx.payee
        assert tx.account_id == account.id
        assert tx.state == TransactionState.APPROVED
        assert tx.category_id == category.id

    @pytest.mark.asyncio
    async def test_combined_filters_with_pagination(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test filters work correctly with pagination."""
        service = TransactionService(db_session)

        # Get first page
        results1, total = await service.search_transactions(
            user_id=user.id,
            limit=2,
            offset=0,
        )

        # Get second page
        results2, _ = await service.search_transactions(
            user_id=user.id,
            limit=2,
            offset=2,
        )

        assert len(results1) == 2
        assert len(results2) == 2
        # Ensure no overlap
        ids1 = {tx.id for tx in results1}
        ids2 = {tx.id for tx in results2}
        assert ids1.isdisjoint(ids2)


class TestTransactionSearchUserIsolation:
    """Tests ensuring search respects user isolation."""

    @pytest.mark.asyncio
    async def test_search_only_returns_user_transactions(
        self,
        db_session: AsyncSession,
        user: User,
        account: Account,
        transactions: list[Transaction],
    ) -> None:
        """Test that search only returns transactions belonging to the user."""
        # Create another user with a transaction
        other_user = User(
            email=f"other_{uuid4()}@example.com",
            password_hash="hashed",
            timezone="UTC",
        )
        db_session.add(other_user)
        await db_session.flush()

        other_account = Account(
            user_id=other_user.id,
            name="Other Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(other_account)
        await db_session.flush()

        other_tx = Transaction(
            user_id=other_user.id,
            account_id=other_account.id,
            date=date(2026, 1, 15),
            payee="Whole Foods Market",  # Same payee as user's transaction
            amount=Decimal("-100.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(other_tx)
        await db_session.flush()

        # Search for "Whole Foods" as the original user
        service = TransactionService(db_session)
        results, total = await service.search_transactions(
            user_id=user.id,
            payee_search="Whole Foods",
        )

        # Should only find the original user's transaction
        assert total == 1
        assert all(tx.user_id == user.id for tx in results)


# ============================================================================
# CRUD Operation Tests
# ============================================================================


class TestCreateTransaction:
    """Tests for creating transactions."""

    @pytest.mark.asyncio
    async def test_create_transaction_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test successfully creating a transaction."""
        service = TransactionService(db_session)
        data = TransactionCreate(
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Store",
            amount=Decimal("-50.00"),
            memo="Test purchase",
        )

        result = await service.create_transaction(user.id, data)

        assert result is not None
        assert result.user_id == user.id
        assert result.account_id == account.id
        assert result.date == date(2026, 1, 15)
        assert result.payee == "Test Store"
        assert result.amount == Decimal("-50.00")
        assert result.memo == "Test purchase"
        assert result.state == TransactionState.INBOX
        assert result.category_id is None

    @pytest.mark.asyncio
    async def test_create_transaction_with_category(
        self, db_session: AsyncSession, user: User, account: Account, category: Category
    ) -> None:
        """Test creating a transaction with a category."""
        service = TransactionService(db_session)
        data = TransactionCreate(
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-75.00"),
            category_id=category.id,
        )

        result = await service.create_transaction(user.id, data)

        assert result is not None
        assert result.category_id == category.id

    @pytest.mark.asyncio
    async def test_create_transaction_nonexistent_account(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test creating transaction with nonexistent account returns None."""
        service = TransactionService(db_session)
        data = TransactionCreate(
            account_id=uuid4(),
            date=date(2026, 1, 15),
            payee="Test Store",
            amount=Decimal("-50.00"),
        )

        result = await service.create_transaction(user.id, data)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_transaction_other_user_account(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test creating transaction with another user's account returns None."""
        # Create another user
        other_user = User(
            email=f"other_create_{uuid4()}@example.com",
            password_hash="hashed",
            timezone="UTC",
        )
        db_session.add(other_user)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionCreate(
            account_id=account.id,  # Belongs to user, not other_user
            date=date(2026, 1, 15),
            payee="Test Store",
            amount=Decimal("-50.00"),
        )

        result = await service.create_transaction(other_user.id, data)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_transaction_nonexistent_category(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test creating transaction with nonexistent category returns None."""
        service = TransactionService(db_session)
        data = TransactionCreate(
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Store",
            amount=Decimal("-50.00"),
            category_id=uuid4(),
        )

        result = await service.create_transaction(user.id, data)

        assert result is None


class TestGetTransaction:
    """Tests for getting a single transaction."""

    @pytest.mark.asyncio
    async def test_get_transaction_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test getting an existing transaction."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.get_transaction(user.id, tx.id)

        assert result is not None
        assert result.id == tx.id
        assert result.payee == "Test Store"

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test getting nonexistent transaction returns None."""
        service = TransactionService(db_session)
        result = await service.get_transaction(user.id, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_transaction_other_user(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test getting another user's transaction returns None."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)

        other_user = User(
            email=f"other_get_{uuid4()}@example.com",
            password_hash="hashed",
            timezone="UTC",
        )
        db_session.add(other_user)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.get_transaction(other_user.id, tx.id)

        assert result is None


class TestUpdateTransaction:
    """Tests for updating transactions."""

    @pytest.mark.asyncio
    async def test_update_transaction_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test successfully updating a transaction."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Original Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionUpdate(
            payee="Updated Store",
            amount=Decimal("-75.00"),
            memo="Updated memo",
        )
        result = await service.update_transaction(user.id, tx.id, data)

        assert result is not None
        assert result.payee == "Updated Store"
        assert result.amount == Decimal("-75.00")
        assert result.memo == "Updated memo"

    @pytest.mark.asyncio
    async def test_update_transaction_partial(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test partial update only changes specified fields."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Original Store",
            amount=Decimal("-50.00"),
            memo="Original memo",
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionUpdate(payee="Updated Store")
        result = await service.update_transaction(user.id, tx.id, data)

        assert result is not None
        assert result.payee == "Updated Store"
        assert result.amount == Decimal("-50.00")  # Unchanged
        assert result.memo == "Original memo"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_transaction_with_category(
        self, db_session: AsyncSession, user: User, account: Account, category: Category
    ) -> None:
        """Test updating transaction with a category."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionUpdate(category_id=category.id)
        result = await service.update_transaction(user.id, tx.id, data)

        assert result is not None
        assert result.category_id == category.id

    @pytest.mark.asyncio
    async def test_update_transaction_nonexistent(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test updating nonexistent transaction returns None."""
        service = TransactionService(db_session)
        data = TransactionUpdate(payee="Updated Store")
        result = await service.update_transaction(user.id, uuid4(), data)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_transaction_cleared_raises_error(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test updating cleared transaction raises ValueError."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.CLEARED,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionUpdate(payee="Updated Store")

        with pytest.raises(ValueError, match="Cleared transactions cannot be modified"):
            await service.update_transaction(user.id, tx.id, data)

    @pytest.mark.asyncio
    async def test_update_transaction_nonexistent_category(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test updating transaction with nonexistent category returns None."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionUpdate(category_id=uuid4())
        result = await service.update_transaction(user.id, tx.id, data)

        assert result is None


class TestDeleteTransaction:
    """Tests for deleting transactions."""

    @pytest.mark.asyncio
    async def test_delete_transaction_inbox_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test deleting an inbox transaction."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()
        tx_id = tx.id

        service = TransactionService(db_session)
        result = await service.delete_transaction(user.id, tx_id)

        assert result is True
        # Verify it's deleted
        deleted = await service.get_transaction(user.id, tx_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_transaction_approved_reverses_balance(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test deleting approved transaction reverses account balance."""
        original_balance = account.balance

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.delete_transaction(user.id, tx.id)

        assert result is True
        await db_session.refresh(account)
        # Balance should be reversed (adding back the -50 that was subtracted)
        assert account.balance == original_balance + Decimal("50.00")

    @pytest.mark.asyncio
    async def test_delete_transaction_nonexistent(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test deleting nonexistent transaction returns False."""
        service = TransactionService(db_session)
        result = await service.delete_transaction(user.id, uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_transaction_other_user(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test deleting another user's transaction returns False."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)

        other_user = User(
            email=f"other_delete_{uuid4()}@example.com",
            password_hash="hashed",
            timezone="UTC",
        )
        db_session.add(other_user)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.delete_transaction(other_user.id, tx.id)

        assert result is False


class TestApproveTransaction:
    """Tests for approving transactions."""

    @pytest.mark.asyncio
    async def test_approve_transaction_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test successfully approving an inbox transaction."""
        original_balance = account.balance

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionApprove(category_id=None)
        result = await service.approve_transaction(user.id, tx.id, data)

        assert result is not None
        assert result.state == TransactionState.APPROVED
        assert result.approved_at is not None
        assert result.categorization_source == CategorizationSource.MANUAL

        await db_session.refresh(account)
        assert account.balance == original_balance + Decimal("-50.00")

    @pytest.mark.asyncio
    async def test_approve_transaction_with_category(
        self, db_session: AsyncSession, user: User, account: Account, category: Category
    ) -> None:
        """Test approving transaction with a category."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionApprove(category_id=category.id)
        result = await service.approve_transaction(user.id, tx.id, data)

        assert result is not None
        assert result.category_id == category.id
        assert result.state == TransactionState.APPROVED

    @pytest.mark.asyncio
    async def test_approve_transaction_already_approved(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test approving already approved transaction returns it unchanged."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionApprove(category_id=None)
        result = await service.approve_transaction(user.id, tx.id, data)

        assert result is not None
        assert result.state == TransactionState.APPROVED

    @pytest.mark.asyncio
    async def test_approve_transaction_nonexistent(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test approving nonexistent transaction returns None."""
        service = TransactionService(db_session)
        data = TransactionApprove(category_id=None)
        result = await service.approve_transaction(user.id, uuid4(), data)

        assert result is None

    @pytest.mark.asyncio
    async def test_approve_transaction_nonexistent_category(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test approving transaction with nonexistent category returns None."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        data = TransactionApprove(category_id=uuid4())
        result = await service.approve_transaction(user.id, tx.id, data)

        assert result is None


class TestUnapproveTransaction:
    """Tests for unapproving transactions."""

    @pytest.mark.asyncio
    async def test_unapprove_transaction_success(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test successfully unapproving an approved transaction."""
        original_balance = account.balance

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.unapprove_transaction(user.id, tx.id)

        assert result is not None
        assert result.state == TransactionState.INBOX
        assert result.approved_at is None

        await db_session.refresh(account)
        # Balance should be reversed
        assert account.balance == original_balance + Decimal("50.00")

    @pytest.mark.asyncio
    async def test_unapprove_transaction_not_approved(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test unapproving inbox transaction returns it unchanged."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.unapprove_transaction(user.id, tx.id)

        assert result is not None
        assert result.state == TransactionState.INBOX

    @pytest.mark.asyncio
    async def test_unapprove_transaction_nonexistent(
        self, db_session: AsyncSession, user: User
    ) -> None:
        """Test unapproving nonexistent transaction returns None."""
        service = TransactionService(db_session)
        result = await service.unapprove_transaction(user.id, uuid4())

        assert result is None


class TestBatchApproveTransactions:
    """Tests for batch approving transactions."""

    @pytest.mark.asyncio
    async def test_batch_approve_success(
        self, db_session: AsyncSession, user: User, account: Account, category: Category
    ) -> None:
        """Test batch approving multiple transactions."""
        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store 1",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Store 2",
            amount=Decimal("-75.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2])
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.batch_approve_transactions(
            user.id, [tx1.id, tx2.id], category.id
        )

        assert result.success_count == 2
        assert result.failed_count == 0
        assert result.failed_ids == []

        await db_session.refresh(tx1)
        await db_session.refresh(tx2)
        assert tx1.state == TransactionState.APPROVED
        assert tx2.state == TransactionState.APPROVED
        assert tx1.category_id == category.id
        assert tx2.category_id == category.id

    @pytest.mark.asyncio
    async def test_batch_approve_partial_failure(
        self, db_session: AsyncSession, user: User, account: Account, category: Category
    ) -> None:
        """Test batch approve with some already approved transactions."""
        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store 1",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Store 2",
            amount=Decimal("-75.00"),
            state=TransactionState.APPROVED,  # Already approved
        )
        db_session.add_all([tx1, tx2])
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.batch_approve_transactions(
            user.id, [tx1.id, tx2.id], category.id
        )

        assert result.success_count == 1
        assert result.failed_count == 1
        assert tx2.id in result.failed_ids

    @pytest.mark.asyncio
    async def test_batch_approve_nonexistent_category(
        self, db_session: AsyncSession, user: User, account: Account
    ) -> None:
        """Test batch approve with nonexistent category fails all."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        service = TransactionService(db_session)
        result = await service.batch_approve_transactions(
            user.id, [tx.id], uuid4()
        )

        assert result.success_count == 0
        assert result.failed_count == 1
        assert tx.id in result.failed_ids


class TestListTransactions:
    """Tests for listing transactions."""

    @pytest.mark.asyncio
    async def test_list_transactions_all(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test listing all transactions for a user."""
        service = TransactionService(db_session)
        results, total = await service.list_transactions(user.id)

        assert total == len(transactions)
        assert len(results) == len(transactions)

    @pytest.mark.asyncio
    async def test_list_transactions_by_account(
        self, db_session: AsyncSession, user: User, account: Account, transactions: list[Transaction]
    ) -> None:
        """Test listing transactions filtered by account."""
        service = TransactionService(db_session)
        results, total = await service.list_transactions(user.id, account_id=account.id)

        for tx in results:
            assert tx.account_id == account.id

    @pytest.mark.asyncio
    async def test_list_transactions_by_state(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test listing transactions filtered by state."""
        service = TransactionService(db_session)
        results, total = await service.list_transactions(
            user.id, state=TransactionState.INBOX
        )

        for tx in results:
            assert tx.state == TransactionState.INBOX

    @pytest.mark.asyncio
    async def test_list_transactions_with_pagination(
        self, db_session: AsyncSession, user: User, transactions: list[Transaction]
    ) -> None:
        """Test listing transactions with pagination."""
        service = TransactionService(db_session)

        results1, total = await service.list_transactions(user.id, limit=3, offset=0)
        results2, _ = await service.list_transactions(user.id, limit=3, offset=3)

        assert len(results1) == 3
        assert len(results2) <= 3
        # Ensure no overlap
        ids1 = {tx.id for tx in results1}
        ids2 = {tx.id for tx in results2}
        assert ids1.isdisjoint(ids2)
