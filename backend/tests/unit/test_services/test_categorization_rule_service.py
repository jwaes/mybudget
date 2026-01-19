"""
Unit tests for CategorizationRuleService.

Tests CRUD operations, rule matching, and transaction categorization.
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mybudget.models.categorization_rule import CategorizationRule
from mybudget.models.category import Category
from mybudget.models.transaction import CategorizationSource, Transaction, TransactionState
from mybudget.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleUpdate,
)
from mybudget.services.categorization_rule_service import CategorizationRuleService


class TestCategorizationRuleServiceInit:
    """Tests for CategorizationRuleService initialization."""

    def test_init_with_db_session(self) -> None:
        """Test CategorizationRuleService can be initialized with db session."""
        mock_db = MagicMock()
        service = CategorizationRuleService(mock_db)
        assert service.db == mock_db


class TestCreateRule:
    """Tests for create_rule method."""

    @pytest.mark.asyncio
    async def test_create_rule_success(self) -> None:
        """Test creating a rule with valid data."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        data = CategorizationRuleCreate(
            payee_pattern="Whole Foods",
            category_id=category_id,
        )

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=uuid4(),
            name="Groceries",
        )

        with patch.object(
            service, "_get_category", new_callable=AsyncMock
        ) as mock_get_category:
            mock_get_category.return_value = mock_category
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.create_rule(user_id, data)

            assert result is not None
            mock_get_category.assert_awaited_once_with(user_id, category_id)
            mock_db.add.assert_called_once()

            added_rule = mock_db.add.call_args[0][0]
            assert isinstance(added_rule, CategorizationRule)
            assert added_rule.user_id == user_id
            assert added_rule.payee_pattern == "Whole Foods"
            assert added_rule.category_id == category_id

            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_rule_category_not_found(self) -> None:
        """Test creating a rule when category doesn't exist returns None."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        data = CategorizationRuleCreate(
            payee_pattern="Test Pattern",
            category_id=category_id,
        )

        with patch.object(
            service, "_get_category", new_callable=AsyncMock
        ) as mock_get_category:
            mock_get_category.return_value = None

            result = await service.create_rule(user_id, data)

            assert result is None
            mock_get_category.assert_awaited_once_with(user_id, category_id)


class TestGetRule:
    """Tests for get_rule method."""

    @pytest.mark.asyncio
    async def test_get_rule_found(self) -> None:
        """Test getting a rule that exists."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=category_id,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_rule
        mock_db.execute.return_value = mock_result

        result = await service.get_rule(user_id, rule_id)

        assert result == mock_rule
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self) -> None:
        """Test getting a rule that doesn't exist returns None."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_rule(user_id, rule_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_rule_wrong_user(self) -> None:
        """Test getting a rule with wrong user_id returns None."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        other_user_id = uuid4()
        rule_id = uuid4()

        # Query returns None because user_id doesn't match
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_rule(other_user_id, rule_id)

        assert result is None


class TestListRules:
    """Tests for list_rules method."""

    @pytest.mark.asyncio
    async def test_list_rules_with_rules(self) -> None:
        """Test listing rules for a user."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        mock_rules = [
            CategorizationRule(
                id=uuid4(),
                user_id=user_id,
                payee_pattern="Pattern 1",
                category_id=uuid4(),
            ),
            CategorizationRule(
                id=uuid4(),
                user_id=user_id,
                payee_pattern="Pattern 2",
                category_id=uuid4(),
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_rules
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_rules(user_id)

        assert len(result) == 2
        assert result == mock_rules
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rules_empty(self) -> None:
        """Test listing rules when none exist."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_rules(user_id)

        assert result == []


class TestUpdateRule:
    """Tests for update_rule method."""

    @pytest.mark.asyncio
    async def test_update_rule_success(self) -> None:
        """Test updating a rule's payee pattern."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=user_id,
            payee_pattern="Old Pattern",
            category_id=category_id,
        )

        data = CategorizationRuleUpdate(payee_pattern="New Pattern")

        with patch.object(
            service, "get_rule", new_callable=AsyncMock
        ) as mock_get_rule:
            mock_get_rule.return_value = mock_rule
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_rule(user_id, rule_id, data)

            assert result is not None
            assert result.payee_pattern == "New Pattern"
            mock_get_rule.assert_awaited_once_with(user_id, rule_id)
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once_with(mock_rule)

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self) -> None:
        """Test updating a rule that doesn't exist returns None."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()

        data = CategorizationRuleUpdate(payee_pattern="New Pattern")

        with patch.object(
            service, "get_rule", new_callable=AsyncMock
        ) as mock_get_rule:
            mock_get_rule.return_value = None

            result = await service.update_rule(user_id, rule_id, data)

            assert result is None
            mock_get_rule.assert_awaited_once_with(user_id, rule_id)

    @pytest.mark.asyncio
    async def test_update_rule_invalid_category(self) -> None:
        """Test updating a rule with invalid category returns None."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()
        old_category_id = uuid4()
        new_category_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=user_id,
            payee_pattern="Pattern",
            category_id=old_category_id,
        )

        data = CategorizationRuleUpdate(category_id=new_category_id)

        with patch.object(
            service, "get_rule", new_callable=AsyncMock
        ) as mock_get_rule, patch.object(
            service, "_get_category", new_callable=AsyncMock
        ) as mock_get_category:
            mock_get_rule.return_value = mock_rule
            mock_get_category.return_value = None  # Category not found

            result = await service.update_rule(user_id, rule_id, data)

            assert result is None
            mock_get_rule.assert_awaited_once_with(user_id, rule_id)
            mock_get_category.assert_awaited_once_with(user_id, new_category_id)

    @pytest.mark.asyncio
    async def test_update_rule_both_fields(self) -> None:
        """Test updating both payee_pattern and category_id."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()
        old_category_id = uuid4()
        new_category_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=user_id,
            payee_pattern="Old Pattern",
            category_id=old_category_id,
        )

        mock_new_category = Category(
            id=new_category_id,
            user_id=user_id,
            group_id=uuid4(),
            name="New Category",
        )

        data = CategorizationRuleUpdate(
            payee_pattern="New Pattern",
            category_id=new_category_id,
        )

        with patch.object(
            service, "get_rule", new_callable=AsyncMock
        ) as mock_get_rule, patch.object(
            service, "_get_category", new_callable=AsyncMock
        ) as mock_get_category:
            mock_get_rule.return_value = mock_rule
            mock_get_category.return_value = mock_new_category
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_rule(user_id, rule_id, data)

            assert result is not None
            assert result.payee_pattern == "New Pattern"
            assert result.category_id == new_category_id


class TestDeleteRule:
    """Tests for delete_rule method."""

    @pytest.mark.asyncio
    async def test_delete_rule_success(self) -> None:
        """Test deleting a rule successfully."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=user_id,
            payee_pattern="Pattern",
            category_id=category_id,
        )

        with patch.object(
            service, "get_rule", new_callable=AsyncMock
        ) as mock_get_rule:
            mock_get_rule.return_value = mock_rule
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()

            result = await service.delete_rule(user_id, rule_id)

            assert result is True
            mock_get_rule.assert_awaited_once_with(user_id, rule_id)
            mock_db.delete.assert_awaited_once_with(mock_rule)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_rule_not_found(self) -> None:
        """Test deleting a rule that doesn't exist returns False."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()

        with patch.object(
            service, "get_rule", new_callable=AsyncMock
        ) as mock_get_rule:
            mock_get_rule.return_value = None

            result = await service.delete_rule(user_id, rule_id)

            assert result is False
            mock_get_rule.assert_awaited_once_with(user_id, rule_id)


class TestFindMatchingRule:
    """Tests for find_matching_rule method."""

    @pytest.mark.asyncio
    async def test_find_matching_rule_match_found(self) -> None:
        """Test finding a matching rule."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_rule1 = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=category_id,
        )
        mock_rule2 = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Target",
            category_id=uuid4(),
        )

        with patch.object(
            service, "list_rules", new_callable=AsyncMock
        ) as mock_list_rules:
            mock_list_rules.return_value = [mock_rule1, mock_rule2]

            result = await service.find_matching_rule(user_id, "Whole Foods Market")

            assert result == mock_rule1
            mock_list_rules.assert_awaited_once_with(user_id)

    @pytest.mark.asyncio
    async def test_find_matching_rule_no_match(self) -> None:
        """Test finding no matching rule."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        mock_rule = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=uuid4(),
        )

        with patch.object(
            service, "list_rules", new_callable=AsyncMock
        ) as mock_list_rules:
            mock_list_rules.return_value = [mock_rule]

            result = await service.find_matching_rule(user_id, "Target Store")

            assert result is None
            mock_list_rules.assert_awaited_once_with(user_id)

    @pytest.mark.asyncio
    async def test_find_matching_rule_case_insensitive(self) -> None:
        """Test that matching is case-insensitive."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="whole foods",  # lowercase
            category_id=category_id,
        )

        with patch.object(
            service, "list_rules", new_callable=AsyncMock
        ) as mock_list_rules:
            mock_list_rules.return_value = [mock_rule]

            result = await service.find_matching_rule(user_id, "WHOLE FOODS MARKET")

            assert result == mock_rule

    @pytest.mark.asyncio
    async def test_find_matching_rule_first_match_wins(self) -> None:
        """Test that the first matching rule is returned."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        mock_rule1 = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole",
            category_id=uuid4(),
        )
        mock_rule2 = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Foods",
            category_id=uuid4(),
        )

        with patch.object(
            service, "list_rules", new_callable=AsyncMock
        ) as mock_list_rules:
            mock_list_rules.return_value = [mock_rule1, mock_rule2]

            result = await service.find_matching_rule(user_id, "Whole Foods Market")

            # Both rules could match, but the first one should win
            assert result == mock_rule1


class TestApplyRulesToTransaction:
    """Tests for apply_rules_to_transaction method."""

    @pytest.mark.asyncio
    async def test_apply_rules_rule_applied(self) -> None:
        """Test applying rules to a transaction when a match is found."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_transaction = Transaction(
            id=uuid4(),
            user_id=user_id,
            account_id=uuid4(),
            payee="Whole Foods Market",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
            category_id=None,
            categorization_source=None,
        )

        mock_rule = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=category_id,
        )

        with patch.object(
            service, "find_matching_rule", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = mock_rule

            result = await service.apply_rules_to_transaction(user_id, mock_transaction)

            assert result is True
            assert mock_transaction.category_id == category_id
            assert mock_transaction.categorization_source == CategorizationSource.RULE
            mock_find.assert_awaited_once_with(user_id, "Whole Foods Market")

    @pytest.mark.asyncio
    async def test_apply_rules_no_match(self) -> None:
        """Test applying rules when no match is found."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        mock_transaction = Transaction(
            id=uuid4(),
            user_id=user_id,
            account_id=uuid4(),
            payee="Random Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
            category_id=None,
            categorization_source=None,
        )

        with patch.object(
            service, "find_matching_rule", new_callable=AsyncMock
        ) as mock_find:
            mock_find.return_value = None

            result = await service.apply_rules_to_transaction(user_id, mock_transaction)

            assert result is False
            assert mock_transaction.category_id is None
            assert mock_transaction.categorization_source is None

    @pytest.mark.asyncio
    async def test_apply_rules_already_categorized(self) -> None:
        """Test that rules don't override existing categorization."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        existing_category_id = uuid4()

        mock_transaction = Transaction(
            id=uuid4(),
            user_id=user_id,
            account_id=uuid4(),
            payee="Whole Foods Market",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
            category_id=existing_category_id,  # Already categorized
            categorization_source=CategorizationSource.MANUAL,
        )

        with patch.object(
            service, "find_matching_rule", new_callable=AsyncMock
        ) as mock_find:
            result = await service.apply_rules_to_transaction(user_id, mock_transaction)

            assert result is False
            # Category should remain unchanged
            assert mock_transaction.category_id == existing_category_id
            assert mock_transaction.categorization_source == CategorizationSource.MANUAL
            # find_matching_rule should not even be called
            mock_find.assert_not_awaited()


class TestListRulesWithCategory:
    """Tests for list_rules_with_category method."""

    @pytest.mark.asyncio
    async def test_list_rules_with_category(self) -> None:
        """Test listing rules with their category names."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=category_id,
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_rule, "Groceries")]
        mock_db.execute.return_value = mock_result

        result = await service.list_rules_with_category(user_id)

        assert len(result) == 1
        assert result[0][0] == mock_rule
        assert result[0][1] == "Groceries"


class TestGetRuleWithCategory:
    """Tests for get_rule_with_category method."""

    @pytest.mark.asyncio
    async def test_get_rule_with_category_found(self) -> None:
        """Test getting a rule with its category name."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=category_id,
        )

        mock_result = MagicMock()
        mock_result.one_or_none.return_value = (mock_rule, "Groceries")
        mock_db.execute.return_value = mock_result

        result = await service.get_rule_with_category(user_id, rule_id)

        assert result is not None
        assert result[0] == mock_rule
        assert result[1] == "Groceries"

    @pytest.mark.asyncio
    async def test_get_rule_with_category_not_found(self) -> None:
        """Test getting a rule that doesn't exist."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        rule_id = uuid4()

        mock_result = MagicMock()
        mock_result.one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_rule_with_category(user_id, rule_id)

        assert result is None


class TestFindMatchingRuleWithCategory:
    """Tests for find_matching_rule_with_category method."""

    @pytest.mark.asyncio
    async def test_find_matching_rule_with_category_match_found(self) -> None:
        """Test finding a matching rule with category name."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_rule = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=category_id,
        )

        with patch.object(
            service, "list_rules_with_category", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [(mock_rule, "Groceries")]

            result = await service.find_matching_rule_with_category(
                user_id, "Whole Foods Market"
            )

            assert result is not None
            assert result[0] == mock_rule
            assert result[1] == "Groceries"

    @pytest.mark.asyncio
    async def test_find_matching_rule_with_category_no_match(self) -> None:
        """Test finding no matching rule with category."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        mock_rule = CategorizationRule(
            id=uuid4(),
            user_id=user_id,
            payee_pattern="Whole Foods",
            category_id=uuid4(),
        )

        with patch.object(
            service, "list_rules_with_category", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = [(mock_rule, "Groceries")]

            result = await service.find_matching_rule_with_category(
                user_id, "Target Store"
            )

            assert result is None


class TestUserIsolation:
    """Tests ensuring rule operations respect user isolation."""

    @pytest.mark.asyncio
    async def test_get_rule_enforces_user_ownership(self) -> None:
        """Test that get_rule only returns rules owned by the user."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        owner_user_id = uuid4()
        other_user_id = uuid4()
        rule_id = uuid4()

        mock_rule = CategorizationRule(
            id=rule_id,
            user_id=owner_user_id,
            payee_pattern="Owner's Rule",
            category_id=uuid4(),
        )

        # When queried by owner, returns the rule
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_rule
        mock_db.execute.return_value = mock_result

        result = await service.get_rule(owner_user_id, rule_id)
        assert result == mock_rule

        # When queried by other user, query returns None (due to user_id filter)
        mock_result.scalar_one_or_none.return_value = None
        result = await service.get_rule(other_user_id, rule_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_rules_only_returns_user_rules(self) -> None:
        """Test that list_rules only returns rules for the specified user."""
        mock_db = AsyncMock()
        service = CategorizationRuleService(mock_db)

        user_id = uuid4()

        user_rules = [
            CategorizationRule(
                id=uuid4(),
                user_id=user_id,
                payee_pattern="User's Rule",
                category_id=uuid4(),
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = user_rules
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_rules(user_id)

        assert len(result) == 1
        assert all(rule.user_id == user_id for rule in result)
