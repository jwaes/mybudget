"""
Budget service.

Provides budget month view calculations and fund assignment operations.
"""
from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.category import Category, CategoryGroup
from mybudget.models.assignment import Assignment
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.account import Account
from mybudget.lib.date_utils import get_month_first_day


class BudgetService:
    """Service for budget calculations and operations."""

    def __init__(self, db: AsyncSession):
        """Initialize budget service with database session."""
        self.db = db

    async def get_funded_this_month(
        self, category_id: UUID, month: date
    ) -> Decimal:
        """
        Get the total amount funded to a category for a specific month.

        Args:
            category_id: The category UUID
            month: The month (should be first day of month)

        Returns:
            Sum of all assignments for the category in the month
        """
        month_start = get_month_first_day(month)

        result = await self.db.execute(
            select(func.coalesce(func.sum(Assignment.amount), 0)).where(
                Assignment.category_id == category_id,
                Assignment.month == month_start,
            )
        )
        return Decimal(str(result.scalar_one()))

    async def get_activity(
        self, category_id: UUID, month: date
    ) -> Decimal:
        """
        Get the total transaction activity for a category in a month.

        Activity = sum of approved transaction amounts.
        Negative amounts = spending, positive = refunds.

        Args:
            category_id: The category UUID
            month: The month (should be first day of month)

        Returns:
            Sum of approved transaction amounts (typically negative for spending)
        """
        month_start = get_month_first_day(month)
        # Calculate month end (last day of month)
        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(month_start.year, month_start.month + 1, 1)

        result = await self.db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.category_id == category_id,
                Transaction.state == TransactionState.APPROVED,
                Transaction.date >= month_start,
                Transaction.date < next_month,
            )
        )
        return Decimal(str(result.scalar_one()))

    async def get_available(
        self, category_id: UUID, month: date
    ) -> Decimal:
        """
        Get the available balance for a category at a given month.

        Available = rollover from all previous months + funded_this_month + activity_this_month

        Rollover = sum of all (funded - spent) from months before `month`

        Args:
            category_id: The category UUID
            month: The month to calculate available for

        Returns:
            Available balance for the category
        """
        month_start = get_month_first_day(month)

        # Get rollover: all assignments before this month minus all activity before this month
        # Rollover = sum(assignments before month) + sum(activity before month)
        # Activity is typically negative for spending

        # All assignments before this month
        assign_before = await self.db.execute(
            select(func.coalesce(func.sum(Assignment.amount), 0)).where(
                Assignment.category_id == category_id,
                Assignment.month < month_start,
            )
        )
        rollover_funded = Decimal(str(assign_before.scalar_one()))

        # All activity before this month
        tx_before = await self.db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.category_id == category_id,
                Transaction.state == TransactionState.APPROVED,
                Transaction.date < month_start,
            )
        )
        rollover_activity = Decimal(str(tx_before.scalar_one()))

        rollover = rollover_funded + rollover_activity

        # This month's funded and activity
        funded_this_month = await self.get_funded_this_month(category_id, month)
        activity_this_month = await self.get_activity(category_id, month)

        return rollover + funded_this_month + activity_this_month

    async def get_category_budget_info(
        self, category_id: UUID, month: date
    ) -> dict[str, Any]:
        """
        Get complete budget info for a category in a month.

        Args:
            category_id: The category UUID
            month: The month

        Returns:
            Dict with funded_this_month, activity, available
        """
        funded = await self.get_funded_this_month(category_id, month)
        activity = await self.get_activity(category_id, month)
        available = await self.get_available(category_id, month)

        return {
            "funded_this_month": funded,
            "activity": activity,
            "available": available,
        }

    async def get_to_assign(self, user_id: UUID, month: date) -> Decimal:
        """
        Calculate "To Assign" amount for a user in a month.

        To Assign = Total account balances - Total assigned across all months

        This represents money in accounts that hasn't been assigned to categories.

        Args:
            user_id: The user UUID
            month: The month (for context, but To Assign is cumulative)

        Returns:
            Amount available to assign
        """
        # Total account balances
        result = await self.db.execute(
            select(func.coalesce(func.sum(Account.balance), 0)).where(
                Account.user_id == user_id
            )
        )
        total_balance = Decimal(str(result.scalar_one()))

        # Total ever assigned (all assignments, all months, all categories)
        result = await self.db.execute(
            select(func.coalesce(func.sum(Assignment.amount), 0)).where(
                Assignment.user_id == user_id
            )
        )
        total_assigned = Decimal(str(result.scalar_one()))

        return total_balance - total_assigned

    async def get_month_view(self, user_id: UUID, month: date) -> dict[str, Any]:
        """
        Get complete budget month view for a user.

        Returns all category groups with their categories, each with
        funded_this_month, activity, and available amounts.

        Args:
            user_id: The user UUID
            month: The month to view

        Returns:
            Dict with month, to_assign, groups (with categories and budget info)
        """
        month_start = get_month_first_day(month)

        # Get all category groups ordered by display_order
        groups_result = await self.db.execute(
            select(CategoryGroup)
            .where(CategoryGroup.user_id == user_id)
            .order_by(CategoryGroup.display_order)
        )
        groups = groups_result.scalars().all()

        groups_data = []
        for group in groups:
            # Get categories in this group
            cats_result = await self.db.execute(
                select(Category)
                .where(Category.group_id == group.id)
                .order_by(Category.name)
            )
            categories = cats_result.scalars().all()

            cats_data = []
            for cat in categories:
                budget_info = await self.get_category_budget_info(cat.id, month_start)
                cats_data.append({
                    "id": str(cat.id),
                    "name": cat.name,
                    "funded_this_month": str(budget_info["funded_this_month"]),
                    "activity": str(budget_info["activity"]),
                    "available": str(budget_info["available"]),
                })

            groups_data.append({
                "id": str(group.id),
                "name": group.name,
                "display_order": group.display_order,
                "categories": cats_data,
            })

        to_assign = await self.get_to_assign(user_id, month_start)

        return {
            "month": month_start.strftime("%Y-%m"),
            "to_assign": str(to_assign),
            "groups": groups_data,
        }

    async def assign_funds(
        self,
        user_id: UUID,
        category_id: UUID,
        amount: Decimal,
        month: date,
    ) -> Assignment:
        """
        Assign (or unassign) funds to a category for a month.

        Creates an append-only assignment record.
        Positive amounts assign funds, negative amounts unassign.

        Args:
            user_id: The user UUID
            category_id: The target category UUID
            amount: Amount to assign (positive) or unassign (negative)
            month: The month to assign funds to

        Returns:
            The created Assignment record
        """
        month_start = get_month_first_day(month)

        assignment = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            month=month_start,
        )
        self.db.add(assignment)
        await self.db.flush()

        return assignment
