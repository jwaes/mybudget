"""
Target service for managing spending targets.
"""
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.date_utils import get_month_first_day
from mybudget.models.category import Category
from mybudget.models.target import CategoryTarget, TargetType
from mybudget.schemas.target import (
    CategoryTargetCreate,
    CategoryTargetUpdate,
)
from mybudget.services.budget_service import BudgetService


class TargetService:
    """Service for category target operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.budget_service = BudgetService(db)

    async def create_target(
        self, user_id: UUID, data: CategoryTargetCreate
    ) -> CategoryTarget | None:
        """
        Create a new category target.

        Returns None if the category doesn't exist or doesn't belong to user.
        Raises ValueError if category already has a target.
        """
        # Verify category exists and belongs to user
        category = await self._get_category(user_id, data.category_id)
        if not category:
            return None

        # Check if category already has a target
        existing = await self.get_target_by_category(user_id, data.category_id)
        if existing:
            raise ValueError("Category already has a target")

        target = CategoryTarget(
            user_id=user_id,
            category_id=data.category_id,
            target_type=data.target_type,
            amount=data.amount,
            target_date=data.target_date,
        )

        self.db.add(target)
        await self.db.commit()
        await self.db.refresh(target)

        return target

    async def get_target(
        self, user_id: UUID, target_id: UUID
    ) -> CategoryTarget | None:
        """Get target by ID."""
        stmt = select(CategoryTarget).where(
            CategoryTarget.id == target_id,
            CategoryTarget.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_target_by_category(
        self, user_id: UUID, category_id: UUID
    ) -> CategoryTarget | None:
        """Get target for a specific category."""
        stmt = select(CategoryTarget).where(
            CategoryTarget.category_id == category_id,
            CategoryTarget.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_targets(self, user_id: UUID) -> list[CategoryTarget]:
        """List all targets for a user."""
        stmt = (
            select(CategoryTarget)
            .where(CategoryTarget.user_id == user_id)
            .order_by(CategoryTarget.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_target(
        self, user_id: UUID, target_id: UUID, data: CategoryTargetUpdate
    ) -> CategoryTarget | None:
        """Update a target."""
        target = await self.get_target(user_id, target_id)
        if not target:
            return None

        if data.target_type is not None:
            target.target_type = data.target_type
        if data.amount is not None:
            target.amount = data.amount
        if data.target_date is not None:
            target.target_date = data.target_date

        # Validate target_date constraint after update
        if target.target_type == TargetType.TARGET_BY_DATE and target.target_date is None:
            raise ValueError("target_date is required for TARGET_BY_DATE")
        if target.target_type != TargetType.TARGET_BY_DATE and target.target_date is not None:
            # Clear target_date for non-date targets
            target.target_date = None

        await self.db.commit()
        await self.db.refresh(target)

        return target

    async def delete_target(self, user_id: UUID, target_id: UUID) -> bool:
        """Delete a target."""
        target = await self.get_target(user_id, target_id)
        if not target:
            return False

        await self.db.delete(target)
        await self.db.commit()

        return True

    async def calculate_underfunded(
        self, user_id: UUID, target_id: UUID, month: date
    ) -> dict | None:
        """
        Calculate underfunded amount for a target.

        Returns dict with all underfunded calculation data, or None if target not found.
        """
        target = await self.get_target(user_id, target_id)
        if not target:
            return None

        month_start = get_month_first_day(month)

        # Get budget data from budget service
        funded_this_month = await self.budget_service.get_funded_this_month(
            target.category_id, month_start
        )
        available_now = await self.budget_service.get_available(
            target.category_id, month_start
        )

        # Calculate underfunded using model method
        underfunded = target.calculate_underfunded(
            funded_this_month=funded_this_month,
            available_now=available_now,
            current_month=month_start,
        )

        # Determine status
        if underfunded > Decimal("0"):
            status = "UNDERFUNDED"
        elif target.target_type == TargetType.MONTHLY_NEEDED and funded_this_month > target.amount:
            status = "OVERFUNDED"
        else:
            status = "FUNDED"

        # Build response data
        result = {
            "target_id": target.id,
            "category_id": target.category_id,
            "month": month_start,
            "target_type": target.target_type,
            "target_amount": str(target.amount.quantize(Decimal("0.01"))),
            "funded_this_month": str(funded_this_month.quantize(Decimal("0.01"))),
            "available_now": str(available_now.quantize(Decimal("0.01"))),
            "underfunded": str(underfunded.quantize(Decimal("0.01"))),
            "status": status,
        }

        # Add TARGET_BY_DATE specific fields
        if target.target_type == TargetType.TARGET_BY_DATE:
            result["months_left"] = target._calculate_months_left(month_start)
            suggested = target.get_suggested_monthly(available_now, month_start)
            result["suggested_monthly"] = str(suggested.quantize(Decimal("0.01"))) if suggested else None

        return result

    async def get_category_name(self, user_id: UUID, category_id: UUID) -> str | None:
        """Get category name by ID."""
        category = await self._get_category(user_id, category_id)
        return category.name if category else None

    async def _get_category(
        self, user_id: UUID, category_id: UUID
    ) -> Category | None:
        """Get category by ID (internal helper)."""
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
