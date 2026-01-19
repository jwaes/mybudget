"""
Categorization rule service for business logic operations.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.categorization_rule import CategorizationRule
from mybudget.models.category import Category
from mybudget.models.transaction import CategorizationSource, Transaction
from mybudget.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleUpdate,
)


class CategorizationRuleService:
    """Service for categorization rule operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_rule(
        self, user_id: UUID, data: CategorizationRuleCreate
    ) -> CategorizationRule | None:
        """
        Create a new categorization rule.

        Returns None if the specified category doesn't exist or belong to user.
        """
        # Verify category exists and belongs to user
        category = await self._get_category(user_id, data.category_id)
        if not category:
            return None

        rule = CategorizationRule(
            user_id=user_id,
            payee_pattern=data.payee_pattern,
            category_id=data.category_id,
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        return rule

    async def get_rule(
        self, user_id: UUID, rule_id: UUID
    ) -> CategorizationRule | None:
        """Get rule by ID."""
        stmt = select(CategorizationRule).where(
            CategorizationRule.id == rule_id,
            CategorizationRule.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rules(self, user_id: UUID) -> list[CategorizationRule]:
        """List all rules for user, ordered by creation date."""
        stmt = (
            select(CategorizationRule)
            .where(CategorizationRule.user_id == user_id)
            .order_by(CategorizationRule.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_rules_with_category(
        self, user_id: UUID
    ) -> list[tuple[CategorizationRule, str]]:
        """
        List all rules for user with category names.

        Returns list of (rule, category_name) tuples, ordered by creation date.
        """
        stmt = (
            select(CategorizationRule, Category.name)
            .join(Category, CategorizationRule.category_id == Category.id)
            .where(CategorizationRule.user_id == user_id)
            .order_by(CategorizationRule.created_at)
        )
        result = await self.db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_rule_with_category(
        self, user_id: UUID, rule_id: UUID
    ) -> tuple[CategorizationRule, str] | None:
        """
        Get rule by ID with category name.

        Returns tuple of (rule, category_name) or None if not found.
        """
        stmt = (
            select(CategorizationRule, Category.name)
            .join(Category, CategorizationRule.category_id == Category.id)
            .where(
                CategorizationRule.id == rule_id,
                CategorizationRule.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if row:
            return (row[0], row[1])
        return None

    async def find_matching_rule_with_category(
        self, user_id: UUID, payee: str
    ) -> tuple[CategorizationRule, str] | None:
        """
        Find the first rule that matches the payee, with category name.

        Returns tuple of (rule, category_name) or None if no match.
        """
        rules_with_categories = await self.list_rules_with_category(user_id)
        for rule, category_name in rules_with_categories:
            if rule.matches(payee):
                return (rule, category_name)
        return None

    async def update_rule(
        self, user_id: UUID, rule_id: UUID, data: CategorizationRuleUpdate
    ) -> CategorizationRule | None:
        """
        Update a categorization rule.

        Returns None if the rule doesn't exist, doesn't belong to user,
        or if the new category_id is invalid.
        """
        rule = await self.get_rule(user_id, rule_id)
        if not rule:
            return None

        if data.category_id is not None:
            # Verify new category exists and belongs to user
            category = await self._get_category(user_id, data.category_id)
            if not category:
                return None
            rule.category_id = data.category_id

        if data.payee_pattern is not None:
            rule.payee_pattern = data.payee_pattern

        await self.db.commit()
        await self.db.refresh(rule)

        return rule

    async def delete_rule(self, user_id: UUID, rule_id: UUID) -> bool:
        """Delete a rule. Returns True if deleted."""
        rule = await self.get_rule(user_id, rule_id)
        if not rule:
            return False

        await self.db.delete(rule)
        await self.db.commit()

        return True

    async def find_matching_rule(
        self, user_id: UUID, payee: str
    ) -> CategorizationRule | None:
        """
        Find the first rule that matches the payee.

        Rules are evaluated in creation order (oldest first).
        """
        rules = await self.list_rules(user_id)
        for rule in rules:
            if rule.matches(payee):
                return rule
        return None

    async def apply_rules_to_transaction(
        self, user_id: UUID, transaction: Transaction
    ) -> bool:
        """
        Apply categorization rules to a transaction.

        Sets category_id and categorization_source = RULE if a match is found.
        Does not override existing categorization.

        Returns True if a rule was applied.
        """
        if transaction.category_id is not None:
            # Already categorized, don't override
            return False

        rule = await self.find_matching_rule(user_id, transaction.payee)
        if rule:
            transaction.category_id = rule.category_id
            transaction.categorization_source = CategorizationSource.RULE
            return True
        return False

    async def _get_category(
        self, user_id: UUID, category_id: UUID
    ) -> Category | None:
        """Get category by ID, verifying it belongs to the user."""
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
