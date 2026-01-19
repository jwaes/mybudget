"""
Contract tests for Categorization Rules API endpoints.

Tests CRUD operations for auto-categorization rules.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.categorization_rule import CategorizationRule
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.user import User


@pytest.mark.contract
class TestCreateCategorizationRule:
    """Contract tests for POST /api/rules/ endpoint."""

    @pytest.mark.asyncio
    async def test_create_rule_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a new categorization rule."""
        user = User(
            email="create_rule@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/",
            json={
                "payee_pattern": "Whole Foods",
                "category_id": str(category.id),
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["payee_pattern"] == "Whole Foods"
        assert data["category_id"] == str(category.id)
        assert data["user_id"] == str(user.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_rule_invalid_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a rule with non-existent category returns 400."""
        user = User(
            email="create_rule_invalid@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/",
            json={
                "payee_pattern": "Test Pattern",
                "category_id": str(uuid4()),
            },
            cookies=cookies,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_rule_other_user_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a rule with another user's category returns 400."""
        user1 = User(
            email="create_rule_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="create_rule_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        # Create category for user2
        group = CategoryGroup(user_id=user2.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user2.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        # User1 tries to create rule with user2's category
        token = create_session_token(user1.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/",
            json={
                "payee_pattern": "Test Pattern",
                "category_id": str(category.id),
            },
            cookies=cookies,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_rule_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test creating a rule without authentication returns 401."""
        response = await client.post(
            "/api/rules/",
            json={
                "payee_pattern": "Test Pattern",
                "category_id": str(uuid4()),
            },
        )

        assert response.status_code == 401


@pytest.mark.contract
class TestListCategorizationRules:
    """Contract tests for GET /api/rules/ endpoint."""

    @pytest.mark.asyncio
    async def test_list_rules_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing categorization rules."""
        user = User(
            email="list_rules@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category1 = Category(user_id=user.id, group_id=group.id, name="Groceries")
        category2 = Category(user_id=user.id, group_id=group.id, name="Utilities")
        db_session.add_all([category1, category2])
        await db_session.flush()

        rule1 = CategorizationRule(
            user_id=user.id,
            payee_pattern="Whole Foods",
            category_id=category1.id,
        )
        rule2 = CategorizationRule(
            user_id=user.id,
            payee_pattern="Electric Company",
            category_id=category2.id,
        )
        db_session.add_all([rule1, rule2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/rules/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["rules"]) == 2
        # Verify rules include category names
        patterns = [r["payee_pattern"] for r in data["rules"]]
        assert "Whole Foods" in patterns
        assert "Electric Company" in patterns
        # Verify category names are included
        for rule in data["rules"]:
            assert "category_name" in rule

    @pytest.mark.asyncio
    async def test_list_rules_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing rules when none exist."""
        user = User(
            email="list_rules_empty@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/rules/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["rules"] == []

    @pytest.mark.asyncio
    async def test_list_rules_user_isolation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that users can only see their own rules."""
        user1 = User(
            email="list_rules_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="list_rules_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        # Create categories and rules for both users
        group1 = CategoryGroup(user_id=user1.id, name="Group 1", display_order=0)
        group2 = CategoryGroup(user_id=user2.id, name="Group 2", display_order=0)
        db_session.add_all([group1, group2])
        await db_session.flush()

        category1 = Category(user_id=user1.id, group_id=group1.id, name="Cat1")
        category2 = Category(user_id=user2.id, group_id=group2.id, name="Cat2")
        db_session.add_all([category1, category2])
        await db_session.flush()

        rule1 = CategorizationRule(
            user_id=user1.id,
            payee_pattern="User1 Pattern",
            category_id=category1.id,
        )
        rule2 = CategorizationRule(
            user_id=user2.id,
            payee_pattern="User2 Pattern",
            category_id=category2.id,
        )
        db_session.add_all([rule1, rule2])
        await db_session.flush()

        # User1 should only see their rule
        token1 = create_session_token(user1.id)
        cookies1 = {SESSION_COOKIE_NAME: token1}

        response = await client.get("/api/rules/", cookies=cookies1)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["rules"][0]["payee_pattern"] == "User1 Pattern"


@pytest.mark.contract
class TestGetCategorizationRule:
    """Contract tests for GET /api/rules/{rule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_rule_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a specific rule by ID."""
        user = User(
            email="get_rule@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Whole Foods",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/rules/{rule.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(rule.id)
        assert data["payee_pattern"] == "Whole Foods"
        assert data["category_id"] == str(category.id)
        assert data["category_name"] == "Groceries"

    @pytest.mark.asyncio
    async def test_get_rule_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a non-existent rule returns 404."""
        user = User(
            email="get_rule_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/rules/{uuid4()}", cookies=cookies)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_rule_other_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting another user's rule returns 404."""
        user1 = User(
            email="get_rule_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="get_rule_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        group = CategoryGroup(user_id=user1.id, name="Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user1.id, group_id=group.id, name="Cat")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user1.id,
            payee_pattern="User1 Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        # User2 tries to get user1's rule
        token2 = create_session_token(user2.id)
        cookies2 = {SESSION_COOKIE_NAME: token2}

        response = await client.get(f"/api/rules/{rule.id}", cookies=cookies2)

        assert response.status_code == 404


@pytest.mark.contract
class TestUpdateCategorizationRule:
    """Contract tests for PUT /api/rules/{rule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_rule_payee_pattern(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a rule's payee pattern."""
        user = User(
            email="update_rule@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Old Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/rules/{rule.id}",
            json={"payee_pattern": "New Pattern"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payee_pattern"] == "New Pattern"
        assert data["category_id"] == str(category.id)

    @pytest.mark.asyncio
    async def test_update_rule_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a rule's category."""
        user = User(
            email="update_rule_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category1 = Category(user_id=user.id, group_id=group.id, name="Groceries")
        category2 = Category(user_id=user.id, group_id=group.id, name="Dining")
        db_session.add_all([category1, category2])
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Test Pattern",
            category_id=category1.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/rules/{rule.id}",
            json={"category_id": str(category2.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == str(category2.id)

    @pytest.mark.asyncio
    async def test_update_rule_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a non-existent rule returns 404."""
        user = User(
            email="update_rule_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/rules/{uuid4()}",
            json={"payee_pattern": "New Pattern"},
            cookies=cookies,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_rule_invalid_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a rule with invalid category returns 404."""
        user = User(
            email="update_rule_invalid_cat@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Test Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/rules/{rule.id}",
            json={"category_id": str(uuid4())},
            cookies=cookies,
        )

        assert response.status_code == 404


@pytest.mark.contract
class TestDeleteCategorizationRule:
    """Contract tests for DELETE /api/rules/{rule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_rule_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a rule."""
        user = User(
            email="delete_rule@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Test Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(f"/api/rules/{rule.id}", cookies=cookies)

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/rules/{rule.id}", cookies=cookies)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a non-existent rule returns 404."""
        user = User(
            email="delete_rule_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(f"/api/rules/{uuid4()}", cookies=cookies)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule_other_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting another user's rule returns 404."""
        user1 = User(
            email="delete_rule_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="delete_rule_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        group = CategoryGroup(user_id=user1.id, name="Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user1.id, group_id=group.id, name="Cat")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user1.id,
            payee_pattern="User1 Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        # User2 tries to delete user1's rule
        token2 = create_session_token(user2.id)
        cookies2 = {SESSION_COOKIE_NAME: token2}

        response = await client.delete(f"/api/rules/{rule.id}", cookies=cookies2)

        assert response.status_code == 404


@pytest.mark.contract
class TestTestCategorizationRule:
    """Contract tests for POST /api/rules/test endpoint."""

    @pytest.mark.asyncio
    async def test_test_rule_match_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test rule matching endpoint when a match is found."""
        user = User(
            email="test_rule_match@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Whole Foods",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/test",
            json={"payee": "Whole Foods Market"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payee"] == "Whole Foods Market"
        assert data["matched"] is True
        assert data["rule"] is not None
        assert data["rule"]["payee_pattern"] == "Whole Foods"
        assert data["rule"]["category_id"] == str(category.id)
        assert data["rule"]["category_name"] == "Groceries"

    @pytest.mark.asyncio
    async def test_test_rule_no_match(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test rule matching endpoint when no match is found."""
        user = User(
            email="test_rule_nomatch@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Whole Foods",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/test",
            json={"payee": "Target"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payee"] == "Target"
        assert data["matched"] is False
        assert data["rule"] is None

    @pytest.mark.asyncio
    async def test_test_rule_case_insensitive(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test rule matching is case-insensitive."""
        user = User(
            email="test_rule_case@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="whole foods",  # lowercase
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/test",
            json={"payee": "WHOLE FOODS MARKET"},  # uppercase
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is True

    @pytest.mark.asyncio
    async def test_test_rule_empty_rules(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test rule matching when user has no rules."""
        user = User(
            email="test_rule_empty@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/rules/test",
            json={"payee": "Any Payee"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is False
        assert data["rule"] is None

    @pytest.mark.asyncio
    async def test_test_rule_first_match_wins(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that the first matching rule wins when multiple rules could match."""
        user = User(
            email="test_rule_first@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        groceries = Category(user_id=user.id, group_id=group.id, name="Groceries")
        health = Category(user_id=user.id, group_id=group.id, name="Health")
        db_session.add_all([groceries, health])
        await db_session.flush()

        # Create rules - order matters (created_at determines priority)
        rule1 = CategorizationRule(
            user_id=user.id,
            payee_pattern="Whole",
            category_id=groceries.id,
        )
        db_session.add(rule1)
        await db_session.flush()

        rule2 = CategorizationRule(
            user_id=user.id,
            payee_pattern="Foods",
            category_id=health.id,
        )
        db_session.add(rule2)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Both rules could match "Whole Foods", but the first one (rule1) should win
        response = await client.post(
            "/api/rules/test",
            json={"payee": "Whole Foods"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is True
        assert data["rule"]["category_name"] == "Groceries"
