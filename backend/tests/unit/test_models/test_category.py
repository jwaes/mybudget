"""
Unit tests for Category and CategoryGroup models.

Following TDD principles - test written before implementation.
"""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.user import User


@pytest.mark.unit
class TestCategoryGroupModel:
    """Unit tests for CategoryGroup model."""

    def test_category_group_creation(self) -> None:
        """Test creating a CategoryGroup instance with required fields."""
        from mybudget.models.category import CategoryGroup

        group = CategoryGroup(name="Monthly Bills")

        assert group.name == "Monthly Bills"

    @pytest.mark.asyncio
    async def test_category_group_default_display_order(
        self, db_session: AsyncSession
    ) -> None:
        """Test that default display_order is 0 when inserted."""
        from mybudget.models.category import CategoryGroup

        user = User(email="group_order@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group")

        db_session.add(group)
        await db_session.flush()

        assert group.display_order == 0

    @pytest.mark.asyncio
    async def test_category_group_timestamps_auto_generated(
        self, db_session: AsyncSession
    ) -> None:
        """Test that created_at and updated_at are auto-generated on insert."""
        from mybudget.models.category import CategoryGroup

        user = User(email="group_timestamps@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group")

        db_session.add(group)
        await db_session.flush()

        assert group.created_at is not None
        assert group.updated_at is not None
        assert isinstance(group.created_at, datetime)
        assert isinstance(group.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_category_group_persistence(self, db_session: AsyncSession) -> None:
        """Test that CategoryGroup can be persisted to database."""
        from mybudget.models.category import CategoryGroup

        user = User(email="group_persist@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(
            user_id=user.id,
            name="Daily Living",
            display_order=1,
        )

        db_session.add(group)
        await db_session.commit()
        await db_session.refresh(group)

        stmt = select(CategoryGroup).where(CategoryGroup.id == group.id)
        result = await db_session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.id == group.id
        assert retrieved.user_id == user.id
        assert retrieved.name == "Daily Living"
        assert retrieved.display_order == 1

    @pytest.mark.asyncio
    async def test_category_group_name_unique_per_user(
        self, db_session: AsyncSession
    ) -> None:
        """Test that group names must be unique per user."""
        from mybudget.models.category import CategoryGroup

        user = User(email="group_unique@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group1 = CategoryGroup(user_id=user.id, name="Bills")
        group2 = CategoryGroup(user_id=user.id, name="Bills")

        db_session.add(group1)
        await db_session.commit()

        db_session.add(group2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_category_group_user_cascade_delete(
        self, db_session: AsyncSession
    ) -> None:
        """Test that deleting user cascades to groups."""
        from mybudget.models.category import CategoryGroup

        user = User(email="group_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Cascade Test")
        db_session.add(group)
        await db_session.commit()

        group_id = group.id

        await db_session.delete(user)
        await db_session.commit()

        stmt = select(CategoryGroup).where(CategoryGroup.id == group_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    def test_category_group_repr(self) -> None:
        """Test that CategoryGroup has readable representation."""
        from mybudget.models.category import CategoryGroup

        group = CategoryGroup(name="Test Group")

        repr_str = repr(group)
        assert "CategoryGroup" in repr_str


@pytest.mark.unit
class TestCategoryModel:
    """Unit tests for Category model."""

    def test_category_creation(self) -> None:
        """Test creating a Category instance with required fields."""
        from mybudget.models.category import Category

        category = Category(name="Groceries")

        assert category.name == "Groceries"

    @pytest.mark.asyncio
    async def test_category_timestamps_auto_generated(
        self, db_session: AsyncSession
    ) -> None:
        """Test that created_at and updated_at are auto-generated on insert."""
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="cat_timestamps@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test Group")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")

        db_session.add(category)
        await db_session.flush()

        assert category.created_at is not None
        assert category.updated_at is not None
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_category_persistence(self, db_session: AsyncSession) -> None:
        """Test that Category can be persisted to database."""
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="cat_persist@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Daily Living")
        db_session.add(group)
        await db_session.flush()

        category = Category(
            user_id=user.id,
            group_id=group.id,
            name="Persist Test Category",
        )

        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        stmt = select(Category).where(Category.id == category.id)
        result = await db_session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.id == category.id
        assert retrieved.user_id == user.id
        assert retrieved.group_id == group.id
        assert retrieved.name == "Persist Test Category"

    @pytest.mark.asyncio
    async def test_category_name_unique_per_user(
        self, db_session: AsyncSession
    ) -> None:
        """Test that category names must be unique per user."""
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="cat_unique@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test")
        db_session.add(group)
        await db_session.flush()

        cat1 = Category(user_id=user.id, group_id=group.id, name="Rent")
        cat2 = Category(user_id=user.id, group_id=group.id, name="Rent")

        db_session.add(cat1)
        await db_session.commit()

        db_session.add(cat2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_category_user_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting user cascades to categories."""
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="cat_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Cascade Test")
        db_session.add(category)
        await db_session.commit()

        cat_id = category.id

        await db_session.delete(user)
        await db_session.commit()

        stmt = select(Category).where(Category.id == cat_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_category_group_cascade_delete(self, db_session: AsyncSession) -> None:
        """Test that deleting group cascades to categories."""
        from mybudget.models.category import Category, CategoryGroup

        user = User(email="cat_grp_cascade@example.com", password_hash="hashed_password")
        db_session.add(user)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Delete Me")
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Child Cat")
        db_session.add(category)
        await db_session.commit()

        cat_id = category.id

        await db_session.delete(group)
        await db_session.commit()

        stmt = select(Category).where(Category.id == cat_id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    def test_category_repr(self) -> None:
        """Test that Category has readable representation."""
        from mybudget.models.category import Category

        category = Category(name="Test Category")

        repr_str = repr(category)
        assert "Category" in repr_str
