"""
Funding service.

Provides operations for auto-funding underfunded categories.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.category import Category, CategoryGroup
from mybudget.models.target import CategoryTarget
from mybudget.models.assignment import Assignment
from mybudget.models.account import Account
from mybudget.lib.date_utils import get_month_first_day
from mybudget.services.budget_service import BudgetService


@dataclass
class FundingResult:
    """Result of a single category funding operation."""

    funded_amount: Decimal
    requested_amount: Decimal
    is_partial: bool


@dataclass
class FundAllResult:
    """Result of funding all underfunded categories."""

    total_funded: Decimal
    total_underfunded: Decimal
    categories_funded: int
    funded_categories: list[dict]
    is_partial: bool


class FundingService:
    """Service for auto-funding underfunded categories."""

    def __init__(self, db: AsyncSession):
        """Initialize funding service with database session."""
        self.db = db
        self._budget_service = BudgetService(db)

    async def _get_to_assign(self, user_id: UUID, month: date) -> Decimal:
        """Get To Assign amount for user."""
        return await self._budget_service.get_to_assign(user_id, month)

    async def _create_assignment(
        self,
        user_id: UUID,
        category_id: UUID,
        amount: Decimal,
        month: date,
    ) -> Assignment:
        """Create an assignment record."""
        return await self._budget_service.assign_funds(
            user_id, category_id, amount, month
        )

    async def _get_category_underfunded(
        self,
        user_id: UUID,
        category_id: UUID,
        month: date,
    ) -> Decimal:
        """
        Get underfunded amount for a single category.

        Returns 0 if no target exists for the category.
        """
        month_start = get_month_first_day(month)

        # Get the target for this category
        result = await self.db.execute(
            select(CategoryTarget).where(
                CategoryTarget.user_id == user_id,
                CategoryTarget.category_id == category_id,
            )
        )
        target = result.scalar_one_or_none()

        if not target:
            return Decimal("0.00")

        # Get budget info for the category
        budget_info = await self._budget_service.get_category_budget_info(
            category_id, month_start
        )

        return target.calculate_underfunded(
            funded_this_month=budget_info["funded_this_month"],
            available_now=budget_info["available"],
            current_month=month_start,
        )

    async def _get_all_underfunded(
        self,
        user_id: UUID,
        month: date,
    ) -> list[dict[str, Any]]:
        """
        Get all underfunded categories with their amounts.

        Returns categories ordered by group display_order (priority).
        """
        month_start = get_month_first_day(month)

        # Get all targets for this user with their categories and groups
        result = await self.db.execute(
            select(CategoryTarget, Category, CategoryGroup)
            .join(Category, CategoryTarget.category_id == Category.id)
            .join(CategoryGroup, Category.group_id == CategoryGroup.id)
            .where(CategoryTarget.user_id == user_id)
            .order_by(CategoryGroup.display_order, Category.name)
        )
        rows = result.all()

        underfunded_list = []
        for target, category, group in rows:
            budget_info = await self._budget_service.get_category_budget_info(
                category.id, month_start
            )

            underfunded_amount = target.calculate_underfunded(
                funded_this_month=budget_info["funded_this_month"],
                available_now=budget_info["available"],
                current_month=month_start,
            )

            if underfunded_amount > Decimal("0"):
                underfunded_list.append({
                    "category_id": category.id,
                    "category_name": category.name,
                    "underfunded": underfunded_amount,
                    "priority": group.display_order,
                })

        return underfunded_list

    async def fund_single_category(
        self,
        user_id: UUID,
        category_id: UUID,
        month: date,
    ) -> FundingResult | None:
        """
        Fund a single underfunded category.

        Funds up to the underfunded amount, limited by available To Assign.

        Args:
            user_id: The user UUID
            category_id: The category to fund
            month: The budget month

        Returns:
            FundingResult with amounts funded and partial status,
            or None if category not found
        """
        month_start = get_month_first_day(month)

        # Check if category exists and belongs to user
        result = await self.db.execute(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id,
            )
        )
        category = result.scalar_one_or_none()
        if not category:
            return None

        underfunded = await self._get_category_underfunded(
            user_id, category_id, month_start
        )
        to_assign = await self._get_to_assign(user_id, month_start)

        if underfunded == Decimal("0"):
            return FundingResult(
                funded_amount=Decimal("0.00"),
                requested_amount=Decimal("0.00"),
                is_partial=False,
            )

        if to_assign <= Decimal("0"):
            return FundingResult(
                funded_amount=Decimal("0.00"),
                requested_amount=underfunded,
                is_partial=True,
            )

        fund_amount = min(underfunded, to_assign)
        is_partial = fund_amount < underfunded

        if fund_amount > Decimal("0"):
            await self._create_assignment(
                user_id, category_id, fund_amount, month_start
            )

        return FundingResult(
            funded_amount=fund_amount,
            requested_amount=underfunded,
            is_partial=is_partial,
        )

    async def fund_all_underfunded(
        self,
        user_id: UUID,
        month: date,
    ) -> FundAllResult:
        """
        Fund all underfunded categories in priority order.

        Funds categories in order of their group's display_order.
        Stops when To Assign is exhausted.

        Args:
            user_id: The user UUID
            month: The budget month

        Returns:
            FundAllResult with total amounts and partial status
        """
        month_start = get_month_first_day(month)

        underfunded_categories = await self._get_all_underfunded(
            user_id, month_start
        )
        to_assign = await self._get_to_assign(user_id, month_start)

        if not underfunded_categories:
            return FundAllResult(
                total_funded=Decimal("0.00"),
                total_underfunded=Decimal("0.00"),
                categories_funded=0,
                funded_categories=[],
                is_partial=False,
            )

        total_underfunded = sum(
            cat["underfunded"] for cat in underfunded_categories
        )

        if to_assign <= Decimal("0"):
            return FundAllResult(
                total_funded=Decimal("0.00"),
                total_underfunded=total_underfunded,
                categories_funded=0,
                funded_categories=[],
                is_partial=True,
            )

        remaining = to_assign
        total_funded = Decimal("0.00")
        categories_funded = 0
        funded_categories = []

        for cat in underfunded_categories:
            if remaining <= Decimal("0"):
                break

            fund_amount = min(cat["underfunded"], remaining)

            if fund_amount > Decimal("0"):
                await self._create_assignment(
                    user_id,
                    cat["category_id"],
                    fund_amount,
                    month_start,
                )
                total_funded += fund_amount
                remaining -= fund_amount
                categories_funded += 1
                funded_categories.append({
                    "category_id": str(cat["category_id"]),
                    "category_name": cat["category_name"],
                    "amount_funded": str(fund_amount),
                })

        is_partial = total_funded < total_underfunded

        return FundAllResult(
            total_funded=total_funded,
            total_underfunded=total_underfunded,
            categories_funded=categories_funded,
            funded_categories=funded_categories,
            is_partial=is_partial,
        )

    async def get_underfunded_summary(
        self,
        user_id: UUID,
        month: date,
    ) -> dict[str, Any]:
        """
        Get summary of all underfunded categories.

        Returns:
            Dict with total_underfunded and list of categories
        """
        month_start = get_month_first_day(month)

        underfunded_categories = await self._get_all_underfunded(
            user_id, month_start
        )

        total = sum(
            cat["underfunded"] for cat in underfunded_categories
        ) if underfunded_categories else Decimal("0.00")

        return {
            "total_underfunded": total,
            "categories": underfunded_categories,
        }
