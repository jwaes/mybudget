"""
Contract tests for targets API.

Tests for creating, reading, updating, and deleting category targets,
as well as calculating underfunded amounts.
"""
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import create_session_token, SESSION_COOKIE_NAME
from mybudget.models.user import User
from mybudget.models.category import CategoryGroup, Category


class TestTargetsAPICreate:
    """Tests for POST /targets endpoint."""

    @pytest.mark.asyncio
    async def test_create_monthly_needed_target(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a Monthly Needed target."""
        user = User(
            email="target_create@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Rent")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "MONTHLY_NEEDED",
                "amount": "1200.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == str(category.id)
        assert data["target_type"] == "MONTHLY_NEEDED"
        assert data["amount"] == "1200.00"
        assert data["target_date"] is None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_target_balance_target(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a Target Balance target."""
        user = User(
            email="target_balance@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Savings", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Emergency Fund")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "TARGET_BALANCE",
                "amount": "10000.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["target_type"] == "TARGET_BALANCE"
        assert data["amount"] == "10000.00"
        assert data["target_date"] is None

    @pytest.mark.asyncio
    async def test_create_target_by_date_target(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a Target by Date target."""
        user = User(
            email="target_by_date@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Goals", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Vacation")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "TARGET_BY_DATE",
                "amount": "5000.00",
                "target_date": "2026-12-31",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["target_type"] == "TARGET_BY_DATE"
        assert data["amount"] == "5000.00"
        assert data["target_date"] == "2026-12-31"

    @pytest.mark.asyncio
    async def test_create_target_by_date_requires_date(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that TARGET_BY_DATE requires target_date."""
        user = User(
            email="target_no_date@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Goals", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Trip")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "TARGET_BY_DATE",
                "amount": "3000.00",
            },
            cookies=cookies,
        )

        # Validation error can return 422 (Pydantic) or 400 (custom)
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_target_amount_must_be_positive(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that target amount must be positive."""
        user = User(
            email="target_zero@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Electric")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "MONTHLY_NEEDED",
                "amount": "0.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_target_duplicate_category_returns_409(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that a category can only have one target."""
        user = User(
            email="target_dup@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Water")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Create first target
        response1 = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "MONTHLY_NEEDED",
                "amount": "50.00",
            },
            cookies=cookies,
        )
        assert response1.status_code == 201

        # Try to create second target for same category
        response2 = await client.post(
            "/api/targets/",
            json={
                "category_id": str(category.id),
                "target_type": "TARGET_BALANCE",
                "amount": "100.00",
            },
            cookies=cookies,
        )
        assert response2.status_code == 409

    @pytest.mark.asyncio
    async def test_create_target_requires_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that creating a target requires authentication."""
        response = await client.post(
            "/api/targets/",
            json={
                "category_id": "550e8400-e29b-41d4-a716-446655440000",
                "target_type": "MONTHLY_NEEDED",
                "amount": "100.00",
            },
        )
        assert response.status_code == 401


class TestTargetsAPIRead:
    """Tests for GET /targets endpoints."""

    @pytest.mark.asyncio
    async def test_list_targets(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing all targets for a user."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="target_list@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        cat1 = Category(user_id=user.id, group_id=group.id, name="Rent")
        cat2 = Category(user_id=user.id, group_id=group.id, name="Electric")
        db_session.add_all([cat1, cat2])
        await db_session.flush()

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
            amount=Decimal("100.00"),
        )
        db_session.add_all([target1, target2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/targets/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_target_by_id(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a specific target by ID."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="target_get@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Gas")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("80.00"),
        )
        db_session.add(target)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/targets/{target.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(target.id)
        assert data["amount"] == "80.00"

    @pytest.mark.asyncio
    async def test_get_target_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a non-existent target returns 404."""
        user = User(
            email="target_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/targets/550e8400-e29b-41d4-a716-446655440000",
            cookies=cookies,
        )

        assert response.status_code == 404


class TestTargetsAPIUpdate:
    """Tests for PUT /targets/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_target_amount(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a target amount."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="target_update@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Internet")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("50.00"),
        )
        db_session.add(target)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/targets/{target.id}",
            json={"amount": "60.00"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "60.00"

    @pytest.mark.asyncio
    async def test_update_target_change_type(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test changing target type."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="target_changetype@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Savings", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Car Fund")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("5000.00"),
        )
        db_session.add(target)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/targets/{target.id}",
            json={
                "target_type": "TARGET_BY_DATE",
                "amount": "5000.00",
                "target_date": "2027-06-01",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_type"] == "TARGET_BY_DATE"
        assert data["target_date"] == "2027-06-01"


class TestTargetsAPIDelete:
    """Tests for DELETE /targets/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_target(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a target."""
        from mybudget.models.target import CategoryTarget, TargetType

        user = User(
            email="target_delete@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Phone")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("30.00"),
        )
        db_session.add(target)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(f"/api/targets/{target.id}", cookies=cookies)

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/api/targets/{target.id}", cookies=cookies)
        assert get_response.status_code == 404


class TestTargetsAPIUnderfunded:
    """Tests for GET /targets/{id}/underfunded endpoint."""

    @pytest.mark.asyncio
    async def test_underfunded_monthly_needed(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test underfunded calculation for Monthly Needed target."""
        from mybudget.models.target import CategoryTarget, TargetType
        from mybudget.models.assignment import Assignment

        user = User(
            email="underfunded_monthly@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        # Target: $400/month, funded: $250 -> underfunded: $150
        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("400.00"),
        )
        db_session.add(target)

        assignment = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("250.00"),
            month=date(2026, 1, 1),
        )
        db_session.add(assignment)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/targets/{target.id}/underfunded?month=2026-01-01",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_type"] == "MONTHLY_NEEDED"
        assert data["target_amount"] == "400.00"
        assert data["funded_this_month"] == "250.00"
        assert data["underfunded"] == "150.00"
        assert data["status"] == "UNDERFUNDED"

    @pytest.mark.asyncio
    async def test_underfunded_target_balance(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test underfunded calculation for Target Balance target."""
        from mybudget.models.target import CategoryTarget, TargetType
        from mybudget.models.assignment import Assignment

        user = User(
            email="underfunded_balance@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Savings", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Emergency")
        db_session.add(category)
        await db_session.flush()

        # Target balance: $1000, available: $600 -> underfunded: $400
        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )
        db_session.add(target)

        assignment = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("600.00"),
            month=date(2026, 1, 1),
        )
        db_session.add(assignment)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/targets/{target.id}/underfunded?month=2026-01-01",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_type"] == "TARGET_BALANCE"
        assert data["underfunded"] == "400.00"

    @pytest.mark.asyncio
    async def test_underfunded_target_by_date(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test underfunded calculation for Target by Date target."""
        from mybudget.models.target import CategoryTarget, TargetType
        from mybudget.models.assignment import Assignment

        user = User(
            email="underfunded_bydate@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Goals", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Vacation")
        db_session.add(category)
        await db_session.flush()

        # Target: $1200 by April 2026 (4 months away from Jan)
        # Available: $0, funded this month: $0
        # suggested_monthly = ceil(1200 / 4) = 300
        # underfunded = 300 - 0 = 300
        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 4, 1),
        )
        db_session.add(target)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/targets/{target.id}/underfunded?month=2026-01-01",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_type"] == "TARGET_BY_DATE"
        assert data["months_left"] == 4
        assert data["suggested_monthly"] == "300.00"
        assert data["underfunded"] == "300.00"

    @pytest.mark.asyncio
    async def test_underfunded_fully_funded(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that fully funded category shows underfunded = 0."""
        from mybudget.models.target import CategoryTarget, TargetType
        from mybudget.models.assignment import Assignment

        user = User(
            email="fully_funded@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Utilities")
        db_session.add(category)
        await db_session.flush()

        target = CategoryTarget(
            user_id=user.id,
            category_id=category.id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("100.00"),
        )
        db_session.add(target)

        # Fully funded
        assignment = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("100.00"),
            month=date(2026, 1, 1),
        )
        db_session.add(assignment)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/targets/{target.id}/underfunded?month=2026-01-01",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["underfunded"] == "0.00"
        assert data["status"] == "FUNDED"
