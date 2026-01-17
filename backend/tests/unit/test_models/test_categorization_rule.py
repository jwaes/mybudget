"""
Unit tests for CategorizationRule model.

Following TDD principles - test written before implementation.
"""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.user import User


@pytest.mark.unit
class TestCategorizationRuleModel:
    """Unit tests for CategorizationRule model."""

    def test_rule_creation(self) -> None:
        """Test creating a CategorizationRule instance with required fields."""
        from mybudget.models.categorization_rule import CategorizationRule

        rule = CategorizationRule(
            payee_pattern="Albert Heijn",
        )

        assert rule.payee_pattern == "Albert Heijn"

    @pytest.mark.asyncio
    async def test_rule_timestamps_auto_generated(
        self, db_session: AsyncSession
    ) -> None:
        """Test that created_at and updated_at are auto-generated on insert."""
        from mybudget.models.account import Account, AccountType
        from mybudget.models.categorization_rule import CategorizationRule
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="rule_timestamps@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Albert Heijn",
            category_id=category.id,
        )

        db_session.add(rule)
        await db_session.flush()

        assert rule.created_at is not None
        assert rule.updated_at is not None
        assert isinstance(rule.created_at, datetime)
        assert isinstance(rule.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_rule_persistence(self, db_session: AsyncSession) -> None:
        """Test that CategorizationRule can be persisted to database."""
        from mybudget.models.categorization_rule import CategorizationRule
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="rule_persist@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Food")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Colruyt",
            category_id=category.id,
        )

        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)

        # Query the rule back
        stmt = select(CategorizationRule).where(CategorizationRule.payee_pattern == "Colruyt")
        result = await db_session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.id == rule.id
        assert retrieved.user_id == user.id
        assert retrieved.payee_pattern == "Colruyt"
        assert retrieved.category_id == category.id

    @pytest.mark.asyncio
    async def test_rule_user_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting user cascades to rules."""
        from mybudget.models.categorization_rule import CategorizationRule
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="rule_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Test Cat")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Test Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.commit()

        rule_id = rule.id

        await db_session.delete(user)
        await db_session.commit()

        stmt = select(CategorizationRule).where(CategorizationRule.id == rule_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_rule_category_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting category cascades to rules."""
        from mybudget.models.categorization_rule import CategorizationRule
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="rule_cat_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Delete Me")
        db_session.add(category)
        await db_session.flush()

        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="Pattern",
            category_id=category.id,
        )
        db_session.add(rule)
        await db_session.commit()

        rule_id = rule.id

        await db_session.delete(category)
        await db_session.commit()

        stmt = select(CategorizationRule).where(CategorizationRule.id == rule_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    def test_rule_matches_exact_payee(self) -> None:
        """Test rule matching with exact payee (case-insensitive)."""
        from mybudget.models.categorization_rule import CategorizationRule

        rule = CategorizationRule(payee_pattern="Albert Heijn")

        # Exact match
        assert rule.matches("Albert Heijn") is True
        # Case insensitive
        assert rule.matches("albert heijn") is True
        assert rule.matches("ALBERT HEIJN") is True
        # Pattern contained in payee
        assert rule.matches("Albert Heijn Downtown") is True
        # No match
        assert rule.matches("Colruyt") is False

    def test_rule_matches_partial_payee(self) -> None:
        """Test rule matching with partial payee pattern."""
        from mybudget.models.categorization_rule import CategorizationRule

        rule = CategorizationRule(payee_pattern="Delhaize")

        # Pattern in the middle
        assert rule.matches("AD Delhaize Bruges") is True
        # Pattern at start
        assert rule.matches("Delhaize Fresh") is True
        # Pattern at end
        assert rule.matches("Super Delhaize") is True
        # No match
        assert rule.matches("Carrefour") is False

    def test_rule_repr(self) -> None:
        """Test that CategorizationRule has readable representation."""
        from mybudget.models.categorization_rule import CategorizationRule

        rule = CategorizationRule(payee_pattern="Test Pattern")

        repr_str = repr(rule)
        assert "CategorizationRule" in repr_str
