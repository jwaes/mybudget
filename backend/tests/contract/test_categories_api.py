"""
Contract tests for Categories API endpoints.
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.assignment import Assignment
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.user import User


@pytest.mark.contract
class TestCategoryGroupsAPI:
    """Contract tests for category groups API."""

    @pytest.mark.asyncio
    async def test_create_category_group(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a new category group."""
        user = User(
            email="create_group@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/categories/groups",
            json={"name": "Monthly Bills", "display_order": 1},
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Monthly Bills"
        assert data["display_order"] == 1
        assert data["user_id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_list_category_groups(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing category groups."""
        user = User(
            email="list_groups@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group1 = CategoryGroup(user_id=user.id, name="Bills", display_order=0)
        group2 = CategoryGroup(user_id=user.id, name="Savings", display_order=1)
        db_session.add_all([group1, group2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/categories/groups", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Bills"
        assert data[1]["name"] == "Savings"

    @pytest.mark.asyncio
    async def test_update_category_group(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a category group."""
        user = User(
            email="update_group@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Old Name", display_order=0)
        db_session.add(group)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/categories/groups/{group.id}",
            json={"name": "New Name", "display_order": 5},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["display_order"] == 5

    @pytest.mark.asyncio
    async def test_delete_category_group(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a category group."""
        user = User(
            email="delete_group@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Delete Me", display_order=0)
        db_session.add(group)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(
            f"/api/categories/groups/{group.id}",
            cookies=cookies,
        )

        assert response.status_code == 204


@pytest.mark.contract
class TestCategoriesAPI:
    """Contract tests for categories API."""

    @pytest.mark.asyncio
    async def test_create_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a new category."""
        user = User(
            email="create_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Daily Living", display_order=0)
        db_session.add(group)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/categories/",
            json={"group_id": str(group.id), "name": "Groceries"},
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Groceries"
        assert data["group_id"] == str(group.id)

    @pytest.mark.asyncio
    async def test_create_category_invalid_group(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating category with non-existent group."""
        user = User(
            email="create_cat_invalid@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/categories/",
            json={"group_id": str(uuid4()), "name": "Test"},
            cookies=cookies,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_categories_with_groups(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing categories with their groups."""
        user = User(
            email="list_cats@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Daily Living", display_order=0)
        db_session.add(group)
        await db_session.flush()

        cat1 = Category(user_id=user.id, group_id=group.id, name="Groceries")
        cat2 = Category(user_id=user.id, group_id=group.id, name="Restaurants")
        db_session.add_all([cat1, cat2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/categories/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["total_groups"] == 1
        assert data["total_categories"] == 2
        assert len(data["groups"]) == 1
        assert len(data["groups"][0]["categories"]) == 2

    @pytest.mark.asyncio
    async def test_get_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a category by ID."""
        user = User(
            email="get_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Test Cat")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/categories/{category.id}",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Cat"

    @pytest.mark.asyncio
    async def test_update_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a category."""
        user = User(
            email="update_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Old Name")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/categories/{category.id}",
            json={"name": "New Name"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_delete_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a category."""
        user = User(
            email="delete_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Delete Me")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(
            f"/api/categories/{category.id}",
            cookies=cookies,
        )

        assert response.status_code == 204


@pytest.mark.contract
class TestCategoryAssignmentsAPI:
    """Contract tests for category assignment API."""

    @pytest.mark.asyncio
    async def test_assign_funds_to_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test assigning funds to a category."""
        user = User(
            email="assign_funds@example.com",
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
            f"/api/categories/{category.id}/assign",
            json={"amount": "500.00", "month": "2026-01-01"},
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == str(category.id)
        assert Decimal(data["amount"]) == Decimal("500.00")
        assert data["month"] == "2026-01-01"

    @pytest.mark.asyncio
    async def test_assign_negative_to_unassign(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test unassigning funds with a negative amount."""
        user = User(
            email="unassign_funds@example.com",
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

        # First assign some funds
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

        # Now unassign some funds
        response = await client.post(
            f"/api/categories/{category.id}/assign",
            json={"amount": "-50.00", "month": "2026-01-01"},
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("-50.00")

    @pytest.mark.asyncio
    async def test_assign_zero_amount_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that zero assignment amount is rejected."""
        user = User(
            email="zero_assign@example.com",
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

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/categories/{category.id}/assign",
            json={"amount": "0.00", "month": "2026-01-01"},
            cookies=cookies,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_assign_to_nonexistent_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test assigning to non-existent category returns 404."""
        user = User(
            email="assign_nonexistent@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/categories/{uuid4()}/assign",
            json={"amount": "100.00", "month": "2026-01-01"},
            cookies=cookies,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_category_funded_this_month(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting funded amount for a category in a month."""
        user = User(
            email="funded_month@example.com",
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

        # Create multiple assignments for the month
        a1 = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("100.00"),
            month=date(2026, 1, 1),
        )
        a2 = Assignment(
            user_id=user.id,
            category_id=category.id,
            amount=Decimal("50.00"),
            month=date(2026, 1, 1),
        )
        db_session.add_all([a1, a2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/categories/{category.id}/budget?month=2026-01",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["funded_this_month"]) == Decimal("150.00")
