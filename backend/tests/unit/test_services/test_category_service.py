"""
Unit tests for CategoryService.

Tests category and category group CRUD operations.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mybudget.models.category import Category, CategoryGroup
from mybudget.schemas.category import (
    CategoryCreate,
    CategoryGroupCreate,
    CategoryGroupUpdate,
    CategoryUpdate,
)
from mybudget.services.category_service import CategoryService


class TestCategoryServiceInit:
    """Tests for CategoryService initialization."""

    def test_init_with_db_session(self) -> None:
        """Test CategoryService can be initialized with db session."""
        mock_db = MagicMock()
        service = CategoryService(mock_db)
        assert service.db == mock_db


class TestCreateCategoryGroup:
    """Tests for create_category_group method."""

    @pytest.mark.asyncio
    async def test_create_category_group_success(self) -> None:
        """Test creating a category group with valid data."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        data = CategoryGroupCreate(
            name="Monthly Bills",
            display_order=0,
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.create_category_group(user_id, data)

        mock_db.add.assert_called_once()
        added_group = mock_db.add.call_args[0][0]
        assert isinstance(added_group, CategoryGroup)
        assert added_group.user_id == user_id
        assert added_group.name == "Monthly Bills"
        assert added_group.display_order == 0

        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_category_group_with_custom_order(self) -> None:
        """Test creating a category group with custom display order."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        data = CategoryGroupCreate(
            name="Entertainment",
            display_order=5,
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        await service.create_category_group(user_id, data)

        added_group = mock_db.add.call_args[0][0]
        assert added_group.display_order == 5

    @pytest.mark.asyncio
    async def test_create_category_group_default_order(self) -> None:
        """Test creating a category group with default display order."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        data = CategoryGroupCreate(name="New Group")

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        await service.create_category_group(user_id, data)

        added_group = mock_db.add.call_args[0][0]
        assert added_group.display_order == 0  # Default value


class TestGetCategoryGroup:
    """Tests for get_category_group method."""

    @pytest.mark.asyncio
    async def test_get_category_group_found(self) -> None:
        """Test getting a category group that exists."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="Bills",
            display_order=0,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_group
        mock_db.execute.return_value = mock_result

        result = await service.get_category_group(user_id, group_id)

        assert result == mock_group
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_category_group_not_found(self) -> None:
        """Test getting a category group that doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_category_group(user_id, group_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_category_group_wrong_user(self) -> None:
        """Test that getting a group with wrong user_id returns None."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        other_user_id = uuid4()
        group_id = uuid4()

        # Query returns None because user_id doesn't match
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_category_group(other_user_id, group_id)

        assert result is None


class TestListCategoryGroups:
    """Tests for list_category_groups method."""

    @pytest.mark.asyncio
    async def test_list_category_groups_with_groups(self) -> None:
        """Test listing category groups for a user."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()

        mock_groups = [
            CategoryGroup(
                id=uuid4(),
                user_id=user_id,
                name="Group A",
                display_order=0,
            ),
            CategoryGroup(
                id=uuid4(),
                user_id=user_id,
                name="Group B",
                display_order=1,
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_groups
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_category_groups(user_id)

        assert len(result) == 2
        assert result == mock_groups
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_category_groups_empty(self) -> None:
        """Test listing category groups when none exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_category_groups(user_id)

        assert result == []


class TestUpdateCategoryGroup:
    """Tests for update_category_group method."""

    @pytest.mark.asyncio
    async def test_update_category_group_name(self) -> None:
        """Test updating category group name."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="Old Name",
            display_order=0,
        )

        data = CategoryGroupUpdate(name="New Name")

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_group
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category_group(user_id, group_id, data)

            assert result is not None
            assert result.name == "New Name"
            mock_get.assert_awaited_once_with(user_id, group_id)
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once_with(mock_group)

    @pytest.mark.asyncio
    async def test_update_category_group_display_order(self) -> None:
        """Test updating category group display order."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="Group",
            display_order=0,
        )

        data = CategoryGroupUpdate(display_order=5)

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_group
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category_group(user_id, group_id, data)

            assert result is not None
            assert result.display_order == 5

    @pytest.mark.asyncio
    async def test_update_category_group_both_fields(self) -> None:
        """Test updating both name and display order."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="Old Name",
            display_order=0,
        )

        data = CategoryGroupUpdate(name="New Name", display_order=3)

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_group
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category_group(user_id, group_id, data)

            assert result is not None
            assert result.name == "New Name"
            assert result.display_order == 3

    @pytest.mark.asyncio
    async def test_update_category_group_not_found(self) -> None:
        """Test updating a category group that doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        data = CategoryGroupUpdate(name="New Name")

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.update_category_group(user_id, group_id, data)

            assert result is None
            mock_get.assert_awaited_once_with(user_id, group_id)

    @pytest.mark.asyncio
    async def test_update_category_group_no_changes(self) -> None:
        """Test updating with None values (no changes)."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="Original",
            display_order=2,
        )

        data = CategoryGroupUpdate(name=None, display_order=None)

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_group
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category_group(user_id, group_id, data)

            assert result is not None
            assert result.name == "Original"
            assert result.display_order == 2


class TestDeleteCategoryGroup:
    """Tests for delete_category_group method."""

    @pytest.mark.asyncio
    async def test_delete_category_group_success(self) -> None:
        """Test deleting a category group successfully."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="To Delete",
            display_order=0,
        )

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_group
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()

            result = await service.delete_category_group(user_id, group_id)

            assert result is True
            mock_get.assert_awaited_once_with(user_id, group_id)
            mock_db.delete.assert_awaited_once_with(mock_group)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_category_group_not_found(self) -> None:
        """Test deleting a category group that doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.delete_category_group(user_id, group_id)

            assert result is False
            mock_get.assert_awaited_once_with(user_id, group_id)


class TestCreateCategory:
    """Tests for create_category method."""

    @pytest.mark.asyncio
    async def test_create_category_success(self) -> None:
        """Test creating a category with valid data."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_group = CategoryGroup(
            id=group_id,
            user_id=user_id,
            name="Bills",
            display_order=0,
        )

        data = CategoryCreate(
            group_id=group_id,
            name="Electricity",
        )

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get_group:
            mock_get_group.return_value = mock_group
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.create_category(user_id, data)

            assert result is not None
            mock_get_group.assert_awaited_once_with(user_id, group_id)
            mock_db.add.assert_called_once()

            added_category = mock_db.add.call_args[0][0]
            assert isinstance(added_category, Category)
            assert added_category.user_id == user_id
            assert added_category.group_id == group_id
            assert added_category.name == "Electricity"

            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_category_group_not_found(self) -> None:
        """Test creating a category when group doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        data = CategoryCreate(
            group_id=group_id,
            name="Electricity",
        )

        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get_group:
            mock_get_group.return_value = None

            result = await service.create_category(user_id, data)

            assert result is None
            mock_get_group.assert_awaited_once_with(user_id, group_id)

    @pytest.mark.asyncio
    async def test_create_category_group_wrong_user(self) -> None:
        """Test creating a category when group belongs to different user."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        data = CategoryCreate(
            group_id=group_id,
            name="Electricity",
        )

        # get_category_group returns None because group belongs to other user
        with patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get_group:
            mock_get_group.return_value = None

            result = await service.create_category(user_id, data)

            assert result is None


class TestGetCategory:
    """Tests for get_category method."""

    @pytest.mark.asyncio
    async def test_get_category_found(self) -> None:
        """Test getting a category that exists."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=group_id,
            name="Groceries",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_category
        mock_db.execute.return_value = mock_result

        result = await service.get_category(user_id, category_id)

        assert result == mock_category
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_category_not_found(self) -> None:
        """Test getting a category that doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_category(user_id, category_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_category_wrong_user(self) -> None:
        """Test that getting a category with wrong user_id returns None."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        other_user_id = uuid4()
        category_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_category(other_user_id, category_id)

        assert result is None


class TestListCategories:
    """Tests for list_categories method."""

    @pytest.mark.asyncio
    async def test_list_categories_all(self) -> None:
        """Test listing all categories for a user."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_categories = [
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group_id,
                name="Category A",
            ),
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group_id,
                name="Category B",
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_categories
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_categories(user_id)

        assert len(result) == 2
        assert result == mock_categories
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_categories_by_group(self) -> None:
        """Test listing categories filtered by group."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        mock_categories = [
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group_id,
                name="Category A",
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_categories
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_categories(user_id, group_id=group_id)

        assert len(result) == 1
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_categories_empty(self) -> None:
        """Test listing categories when none exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_categories(user_id)

        assert result == []


class TestUpdateCategory:
    """Tests for update_category method."""

    @pytest.mark.asyncio
    async def test_update_category_name(self) -> None:
        """Test updating category name."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=group_id,
            name="Old Name",
        )

        data = CategoryUpdate(name="New Name")

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_category
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category(user_id, category_id, data)

            assert result is not None
            assert result.name == "New Name"
            mock_get.assert_awaited_once_with(user_id, category_id)
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once_with(mock_category)

    @pytest.mark.asyncio
    async def test_update_category_group_id(self) -> None:
        """Test moving category to a different group."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        old_group_id = uuid4()
        new_group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=old_group_id,
            name="Category",
        )

        mock_new_group = CategoryGroup(
            id=new_group_id,
            user_id=user_id,
            name="New Group",
            display_order=1,
        )

        data = CategoryUpdate(group_id=new_group_id)

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get_cat, patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get_group:
            mock_get_cat.return_value = mock_category
            mock_get_group.return_value = mock_new_group
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category(user_id, category_id, data)

            assert result is not None
            assert result.group_id == new_group_id
            mock_get_cat.assert_awaited_once_with(user_id, category_id)
            mock_get_group.assert_awaited_once_with(user_id, new_group_id)

    @pytest.mark.asyncio
    async def test_update_category_invalid_group_id(self) -> None:
        """Test updating category with invalid group_id returns None."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        group_id = uuid4()
        invalid_group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=group_id,
            name="Category",
        )

        data = CategoryUpdate(group_id=invalid_group_id)

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get_cat, patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get_group:
            mock_get_cat.return_value = mock_category
            mock_get_group.return_value = None  # Group not found

            result = await service.update_category(user_id, category_id, data)

            assert result is None
            mock_get_group.assert_awaited_once_with(user_id, invalid_group_id)

    @pytest.mark.asyncio
    async def test_update_category_not_found(self) -> None:
        """Test updating a category that doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        data = CategoryUpdate(name="New Name")

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.update_category(user_id, category_id, data)

            assert result is None
            mock_get.assert_awaited_once_with(user_id, category_id)

    @pytest.mark.asyncio
    async def test_update_category_both_fields(self) -> None:
        """Test updating both name and group_id."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        old_group_id = uuid4()
        new_group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=old_group_id,
            name="Old Name",
        )

        mock_new_group = CategoryGroup(
            id=new_group_id,
            user_id=user_id,
            name="New Group",
            display_order=1,
        )

        data = CategoryUpdate(name="New Name", group_id=new_group_id)

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get_cat, patch.object(
            service, "get_category_group", new_callable=AsyncMock
        ) as mock_get_group:
            mock_get_cat.return_value = mock_category
            mock_get_group.return_value = mock_new_group
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category(user_id, category_id, data)

            assert result is not None
            assert result.name == "New Name"
            assert result.group_id == new_group_id

    @pytest.mark.asyncio
    async def test_update_category_no_changes(self) -> None:
        """Test updating with None values (no changes)."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=group_id,
            name="Original",
        )

        data = CategoryUpdate(name=None, group_id=None)

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_category
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_category(user_id, category_id, data)

            assert result is not None
            assert result.name == "Original"
            assert result.group_id == group_id


class TestDeleteCategory:
    """Tests for delete_category method."""

    @pytest.mark.asyncio
    async def test_delete_category_success(self) -> None:
        """Test deleting a category successfully."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            group_id=group_id,
            name="To Delete",
        )

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = mock_category
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()

            result = await service.delete_category(user_id, category_id)

            assert result is True
            mock_get.assert_awaited_once_with(user_id, category_id)
            mock_db.delete.assert_awaited_once_with(mock_category)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self) -> None:
        """Test deleting a category that doesn't exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        with patch.object(
            service, "get_category", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = None

            result = await service.delete_category(user_id, category_id)

            assert result is False
            mock_get.assert_awaited_once_with(user_id, category_id)


class TestListGroupsWithCategories:
    """Tests for list_groups_with_categories method."""

    @pytest.mark.asyncio
    async def test_list_groups_with_categories(self) -> None:
        """Test listing all groups with their categories."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group1_id = uuid4()
        group2_id = uuid4()

        mock_groups = [
            CategoryGroup(
                id=group1_id,
                user_id=user_id,
                name="Bills",
                display_order=0,
            ),
            CategoryGroup(
                id=group2_id,
                user_id=user_id,
                name="Living",
                display_order=1,
            ),
        ]

        mock_categories_group1 = [
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group1_id,
                name="Electricity",
            ),
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group1_id,
                name="Water",
            ),
        ]

        mock_categories_group2 = [
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group2_id,
                name="Groceries",
            ),
        ]

        with patch.object(
            service, "list_category_groups", new_callable=AsyncMock
        ) as mock_list_groups, patch.object(
            service, "list_categories", new_callable=AsyncMock
        ) as mock_list_cats:
            mock_list_groups.return_value = mock_groups
            mock_list_cats.side_effect = [
                mock_categories_group1,
                mock_categories_group2,
            ]

            result = await service.list_groups_with_categories(user_id)

            assert len(result) == 2
            assert result[0] == (mock_groups[0], mock_categories_group1)
            assert result[1] == (mock_groups[1], mock_categories_group2)

            mock_list_groups.assert_awaited_once_with(user_id)
            assert mock_list_cats.await_count == 2

    @pytest.mark.asyncio
    async def test_list_groups_with_categories_empty(self) -> None:
        """Test listing when no groups exist."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()

        with patch.object(
            service, "list_category_groups", new_callable=AsyncMock
        ) as mock_list_groups, patch.object(
            service, "list_categories", new_callable=AsyncMock
        ) as mock_list_cats:
            mock_list_groups.return_value = []

            result = await service.list_groups_with_categories(user_id)

            assert result == []
            mock_list_groups.assert_awaited_once_with(user_id)
            mock_list_cats.assert_not_awaited()


class TestUserIsolation:
    """Tests ensuring category operations respect user isolation."""

    @pytest.mark.asyncio
    async def test_get_category_enforces_user_ownership(self) -> None:
        """Test that get_category only returns categories owned by the user."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        owner_user_id = uuid4()
        other_user_id = uuid4()
        category_id = uuid4()
        group_id = uuid4()

        mock_category = Category(
            id=category_id,
            user_id=owner_user_id,
            group_id=group_id,
            name="Owner's Category",
        )

        # When queried by owner, returns the category
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_category
        mock_db.execute.return_value = mock_result

        result = await service.get_category(owner_user_id, category_id)
        assert result == mock_category

        # When queried by other user, query returns None
        mock_result.scalar_one_or_none.return_value = None
        result = await service.get_category(other_user_id, category_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_categories_only_returns_user_categories(self) -> None:
        """Test that list_categories only returns categories for the specified user."""
        mock_db = AsyncMock()
        service = CategoryService(mock_db)

        user_id = uuid4()
        group_id = uuid4()

        user_categories = [
            Category(
                id=uuid4(),
                user_id=user_id,
                group_id=group_id,
                name="User Category",
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = user_categories
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_categories(user_id)

        assert len(result) == 1
        assert all(cat.user_id == user_id for cat in result)
