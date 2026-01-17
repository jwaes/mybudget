"""
Category service for business logic operations.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mybudget.models.category import Category, CategoryGroup
from mybudget.schemas.category import (
    CategoryGroupCreate,
    CategoryGroupUpdate,
    CategoryCreate,
    CategoryUpdate,
)


class CategoryService:
    """Service for category and category group operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    # Category Group operations

    async def create_category_group(
        self, user_id: UUID, data: CategoryGroupCreate
    ) -> CategoryGroup:
        """Create a new category group."""
        group = CategoryGroup(
            user_id=user_id,
            name=data.name,
            display_order=data.display_order,
        )

        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)

        return group

    async def get_category_group(
        self, user_id: UUID, group_id: UUID
    ) -> CategoryGroup | None:
        """Get category group by ID."""
        stmt = select(CategoryGroup).where(
            CategoryGroup.id == group_id,
            CategoryGroup.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_category_groups(
        self, user_id: UUID
    ) -> list[CategoryGroup]:
        """List all category groups for a user, ordered by display_order."""
        stmt = (
            select(CategoryGroup)
            .where(CategoryGroup.user_id == user_id)
            .order_by(CategoryGroup.display_order, CategoryGroup.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_category_group(
        self, user_id: UUID, group_id: UUID, data: CategoryGroupUpdate
    ) -> CategoryGroup | None:
        """Update a category group."""
        group = await self.get_category_group(user_id, group_id)
        if not group:
            return None

        if data.name is not None:
            group.name = data.name
        if data.display_order is not None:
            group.display_order = data.display_order

        await self.db.commit()
        await self.db.refresh(group)

        return group

    async def delete_category_group(
        self, user_id: UUID, group_id: UUID
    ) -> bool:
        """Delete a category group (cascades to categories)."""
        group = await self.get_category_group(user_id, group_id)
        if not group:
            return False

        await self.db.delete(group)
        await self.db.commit()

        return True

    # Category operations

    async def create_category(
        self, user_id: UUID, data: CategoryCreate
    ) -> Category | None:
        """
        Create a new category.

        Returns None if the specified group doesn't exist or belong to user.
        """
        # Verify group exists and belongs to user
        group = await self.get_category_group(user_id, data.group_id)
        if not group:
            return None

        category = Category(
            user_id=user_id,
            group_id=data.group_id,
            name=data.name,
        )

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        return category

    async def get_category(
        self, user_id: UUID, category_id: UUID
    ) -> Category | None:
        """Get category by ID."""
        stmt = select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_categories(
        self, user_id: UUID, group_id: UUID | None = None
    ) -> list[Category]:
        """List all categories for a user, optionally filtered by group."""
        stmt = select(Category).where(Category.user_id == user_id)

        if group_id is not None:
            stmt = stmt.where(Category.group_id == group_id)

        stmt = stmt.order_by(Category.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_category(
        self, user_id: UUID, category_id: UUID, data: CategoryUpdate
    ) -> Category | None:
        """Update a category."""
        category = await self.get_category(user_id, category_id)
        if not category:
            return None

        if data.group_id is not None:
            # Verify new group exists and belongs to user
            group = await self.get_category_group(user_id, data.group_id)
            if not group:
                return None
            category.group_id = data.group_id

        if data.name is not None:
            category.name = data.name

        await self.db.commit()
        await self.db.refresh(category)

        return category

    async def delete_category(
        self, user_id: UUID, category_id: UUID
    ) -> bool:
        """Delete a category."""
        category = await self.get_category(user_id, category_id)
        if not category:
            return False

        await self.db.delete(category)
        await self.db.commit()

        return True

    async def list_groups_with_categories(
        self, user_id: UUID
    ) -> list[tuple[CategoryGroup, list[Category]]]:
        """List all category groups with their categories."""
        groups = await self.list_category_groups(user_id)
        result = []

        for group in groups:
            categories = await self.list_categories(user_id, group.id)
            result.append((group, categories))

        return result
