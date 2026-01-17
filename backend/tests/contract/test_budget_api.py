"""
Contract tests for Budget API endpoints.
"""
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.user import User
from mybudget.models.account import Account, AccountType
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.assignment import Assignment
from mybudget.lib.auth import hash_password
from mybudget.lib.session import create_session_token, SESSION_COOKIE_NAME


@pytest.mark.contract
class TestBudgetMonthViewAPI:
    """Contract tests for budget month view API."""

    @pytest.mark.asyncio
    async def test_get_budget_month_view(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting budget month view with categories and amounts."""
        user = User(
            email="budget_view@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Create account for transactions
        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("1000.00"),
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        # Create category groups and categories
        group1 = CategoryGroup(user_id=user.id, name="Monthly Bills", display_order=0)
        group2 = CategoryGroup(user_id=user.id, name="Daily Living", display_order=1)
        db_session.add_all([group1, group2])
        await db_session.flush()

        cat_rent = Category(user_id=user.id, group_id=group1.id, name="Rent")
        cat_groceries = Category(user_id=user.id, group_id=group2.id, name="Groceries")
        db_session.add_all([cat_rent, cat_groceries])
        await db_session.flush()

        # Create assignments for January 2026
        assign1 = Assignment(
            user_id=user.id,
            category_id=cat_rent.id,
            amount=Decimal("1000.00"),
            month=date(2026, 1, 1),
        )
        assign2 = Assignment(
            user_id=user.id,
            category_id=cat_groceries.id,
            amount=Decimal("300.00"),
            month=date(2026, 1, 1),
        )
        db_session.add_all([assign1, assign2])
        await db_session.flush()

        # Create transactions (activity) for January
        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=cat_groceries.id,
            date=date(2026, 1, 15),
            payee="Supermarket",
            amount=Decimal("-75.50"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx1)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/budget/2026-01", cookies=cookies)

        assert response.status_code == 200
        data = response.json()

        assert data["month"] == "2026-01"
        assert len(data["groups"]) == 2

        # Verify structure includes funded, activity, available
        for group in data["groups"]:
            assert "categories" in group
            for cat in group["categories"]:
                assert "funded_this_month" in cat
                assert "activity" in cat
                assert "available" in cat

    @pytest.mark.asyncio
    async def test_get_budget_month_view_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting budget month view with no data."""
        user = User(
            email="budget_empty@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/budget/2026-01", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["month"] == "2026-01"
        assert data["groups"] == []
        assert Decimal(data["to_assign"]) == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_budget_month_view_with_to_assign(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test budget month view includes To Assign calculation."""
        user = User(
            email="budget_toassign@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Create account with income
        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("2000.00"),
            initial_balance=Decimal("0.00"),
        )
        db_session.add(account)
        await db_session.flush()

        # Create category
        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Rent")
        db_session.add(category)
        await db_session.flush()

        # Add income transaction
        income = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=None,  # Unassigned income
            date=date(2026, 1, 1),
            payee="Employer",
            amount=Decimal("2000.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(income)
        await db_session.flush()

        # Assign only part of it
        assign = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("1000.00"),
            month=date(2026, 1, 1),
        )
        db_session.add(assign)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/budget/2026-01", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        # To Assign should be positive (income - assigned)
        assert "to_assign" in data

    @pytest.mark.asyncio
    async def test_get_budget_month_view_with_rollover(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test budget month view includes rollover from previous month."""
        user = User(
            email="budget_rollover@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("1000.00"),
            initial_balance=Decimal("1000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Electric")
        db_session.add(category)
        await db_session.flush()

        # December assignment
        assign_dec = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("100.00"),
            month=date(2025, 12, 1),
        )
        # January assignment
        assign_jan = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("50.00"),
            month=date(2026, 1, 1),
        )
        db_session.add_all([assign_dec, assign_jan])
        await db_session.flush()

        # December expense (only 60 of 100)
        tx_dec = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2025, 12, 15),
            payee="Power Company",
            amount=Decimal("-60.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx_dec)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/budget/2026-01", cookies=cookies)

        assert response.status_code == 200
        data = response.json()

        # Find the Electric category
        electric_cat = None
        for group in data["groups"]:
            for cat in group["categories"]:
                if cat["name"] == "Electric":
                    electric_cat = cat
                    break

        assert electric_cat is not None
        # Available should include rollover: 40 (from Dec) + 50 (Jan funded) = 90
        assert Decimal(electric_cat["available"]) == Decimal("90.00")

    @pytest.mark.asyncio
    async def test_get_budget_invalid_month_format(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test budget month view with invalid month format."""
        user = User(
            email="budget_invalid@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/budget/invalid", cookies=cookies)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_budget_requires_auth(
        self, client: AsyncClient
    ) -> None:
        """Test budget month view requires authentication."""
        response = await client.get("/api/budget/2026-01")
        assert response.status_code == 401


@pytest.mark.contract
class TestUnderfundedSummaryAPI:
    """Contract tests for underfunded summary API (T142)."""

    @pytest.mark.asyncio
    async def test_get_underfunded_summary(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting underfunded summary for a month."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="underfunded_summary@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("5000.00"),
            initial_balance=Decimal("5000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        cat1 = Category(user_id=user.id, group_id=group.id, name="Rent")
        cat2 = Category(user_id=user.id, group_id=group.id, name="Utilities")
        db_session.add_all([cat1, cat2])
        await db_session.flush()

        # Create targets
        target1 = CategoryTarget(
            user_id=user.id,
            category_id=cat1.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("1200.00"),
        )
        target2 = CategoryTarget(
            user_id=user.id,
            category_id=cat2.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("150.00"),
        )
        db_session.add_all([target1, target2])
        await db_session.flush()

        # Assign partial amounts
        assign1 = Assignment(
            user_id=user.id,
            category_id=cat1.id,
            amount=Decimal("800.00"),  # 400 underfunded
            month=date(2026, 1, 1),
        )
        assign2 = Assignment(
            user_id=user.id,
            category_id=cat2.id,
            amount=Decimal("50.00"),  # 100 underfunded
            month=date(2026, 1, 1),
        )
        db_session.add_all([assign1, assign2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/budget/2026-01/underfunded-summary",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_underfunded" in data
        assert "categories_underfunded" in data
        assert "categories" in data
        # Total underfunded = 400 + 100 = 500
        assert Decimal(data["total_underfunded"]) == Decimal("500.00")
        assert data["categories_underfunded"] == 2

    @pytest.mark.asyncio
    async def test_get_underfunded_summary_no_targets(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test underfunded summary with no targets returns zeros."""
        user = User(
            email="no_targets@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/budget/2026-01/underfunded-summary",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_underfunded"]) == Decimal("0")
        assert data["categories_underfunded"] == 0


@pytest.mark.contract
class TestFundUnderfundedAPI:
    """Contract tests for fund underfunded category API (T143)."""

    @pytest.mark.asyncio
    async def test_fund_underfunded_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test funding an underfunded category."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="fund_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("5000.00"),
            initial_balance=Decimal("5000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Rent")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("1000.00"),
        )
        db_session.add(target)
        await db_session.flush()

        # Assign partial
        assign = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("600.00"),
            month=date(2026, 1, 1),
        )
        db_session.add(assign)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/budget/2026-01/fund-underfunded/{category.id}",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "amount_funded" in data
        assert Decimal(data["amount_funded"]) == Decimal("400.00")
        assert data["category_id"] == str(category.id)

    @pytest.mark.asyncio
    async def test_fund_underfunded_partial_when_insufficient(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test partial funding when To Assign is insufficient."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="fund_partial@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Account with limited funds
        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("200.00"),  # Only 200 available
            initial_balance=Decimal("200.00"),
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Rent")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("1000.00"),  # Needs 1000
        )
        db_session.add(target)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/budget/2026-01/fund-underfunded/{category.id}",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        # Should only fund 200 (all available)
        assert Decimal(data["amount_funded"]) == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_fund_underfunded_category_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test funding non-existent category returns 404."""
        user = User(
            email="fund_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        fake_id = "550e8400-e29b-41d4-a716-446655440000"
        response = await client.post(
            f"/api/budget/2026-01/fund-underfunded/{fake_id}",
            cookies=cookies,
        )

        assert response.status_code == 404


@pytest.mark.contract
class TestFundAllUnderfundedAPI:
    """Contract tests for fund all underfunded API (T144)."""

    @pytest.mark.asyncio
    async def test_fund_all_underfunded(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test funding all underfunded categories."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="fund_all@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("5000.00"),
            initial_balance=Decimal("5000.00"),
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        cat1 = Category(user_id=user.id, group_id=group.id, name="Rent")
        cat2 = Category(user_id=user.id, group_id=group.id, name="Utilities")
        db_session.add_all([cat1, cat2])
        await db_session.flush()

        # Create targets
        target1 = CategoryTarget(
            user_id=user.id,
            category_id=cat1.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("500.00"),  # 500 underfunded
        )
        target2 = CategoryTarget(
            user_id=user.id,
            category_id=cat2.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),  # 200 underfunded
        )
        db_session.add_all([target1, target2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/budget/2026-01/fund-all-underfunded",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_funded" in data
        assert "categories_funded" in data
        assert "funded_categories" in data
        # Total should be 500 + 200 = 700
        assert Decimal(data["total_funded"]) == Decimal("700.00")
        assert data["categories_funded"] == 2

    @pytest.mark.asyncio
    async def test_fund_all_partial_when_insufficient(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test partial funding of all when To Assign is insufficient."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="fund_all_partial@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Limited funds
        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=Decimal("300.00"),  # Only 300 available
            initial_balance=Decimal("300.00"),
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        cat1 = Category(user_id=user.id, group_id=group.id, name="Rent")
        cat2 = Category(user_id=user.id, group_id=group.id, name="Utilities")
        db_session.add_all([cat1, cat2])
        await db_session.flush()

        # Create targets totaling more than available
        target1 = CategoryTarget(
            user_id=user.id,
            category_id=cat1.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("500.00"),
        )
        target2 = CategoryTarget(
            user_id=user.id,
            category_id=cat2.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
        )
        db_session.add_all([target1, target2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/budget/2026-01/fund-all-underfunded",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        # Should only fund 300 (all available)
        assert Decimal(data["total_funded"]) == Decimal("300.00")

    @pytest.mark.asyncio
    async def test_fund_all_nothing_underfunded(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test fund all when nothing is underfunded."""
        user = User(
            email="fund_all_none@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/budget/2026-01/fund-all-underfunded",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_funded"]) == Decimal("0")
        assert data["categories_funded"] == 0
