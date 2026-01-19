"""
Unit tests for target service - month rollover behavior.

Tests how targets behave when navigating between months.
Covers User Story 6 - Month Rollover.
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

from mybudget.models.target import CategoryTarget, TargetType


class TestMonthlyNeededRollover:
    """Tests for MONTHLY_NEEDED target month rollover (T157).

    Monthly Needed targets:
    - Underfunded = max(0, target_amount - funded_this_month)
    - When month rolls over, funded_this_month resets to 0
    - So underfunded becomes = target_amount at start of new month
    """

    def test_monthly_needed_underfunded_equals_target_at_month_start(self) -> None:
        """Test that underfunded equals target amount at start of new month."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        # New month, no funding yet
        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("500.00"),  # Available doesn't matter for this type
            current_month=date(2026, 2, 1),
        )

        assert underfunded == Decimal("200.00")

    def test_monthly_needed_funded_this_month_resets_between_months(self) -> None:
        """Test that moving to a new month resets funded_this_month context."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        # January: fully funded
        january_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("200.00"),
            available_now=Decimal("200.00"),
            current_month=date(2026, 1, 1),
        )
        assert january_underfunded == Decimal("0.00")

        # February: funded_this_month resets (caller provides 0)
        february_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),  # Reset for new month
            available_now=Decimal("200.00"),  # Available carries over
            current_month=date(2026, 2, 1),
        )
        assert february_underfunded == Decimal("200.00")

    def test_monthly_needed_partial_funding_shows_remaining(self) -> None:
        """Test partial funding shows remaining underfunded amount."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("75.00"),
            available_now=Decimal("100.00"),
            current_month=date(2026, 1, 1),
        )

        assert underfunded == Decimal("125.00")  # 200 - 75

    def test_monthly_needed_overfunding_returns_zero(self) -> None:
        """Test overfunding returns zero underfunded."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("250.00"),  # More than target
            available_now=Decimal("300.00"),
            current_month=date(2026, 1, 1),
        )

        assert underfunded == Decimal("0")


class TestTargetBalanceRollover:
    """Tests for TARGET_BALANCE target month rollover (T158).

    Target Balance targets:
    - Underfunded = max(0, target_amount - available_now)
    - available_now persists across months (balance carries over)
    - So underfunded adjusts based on current available balance
    """

    def test_target_balance_uses_available_not_funded(self) -> None:
        """Test that target balance uses available balance, not funded amount."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
            target_date=None,
        )

        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("100.00"),  # Funded doesn't matter
            available_now=Decimal("400.00"),
            current_month=date(2026, 1, 1),
        )

        # Underfunded = 1000 - 400 = 600
        assert underfunded == Decimal("600.00")

    def test_target_balance_persists_across_months(self) -> None:
        """Test that available balance carries over between months."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
            target_date=None,
        )

        # January: $400 available
        january_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("400.00"),
            available_now=Decimal("400.00"),
            current_month=date(2026, 1, 1),
        )
        assert january_underfunded == Decimal("600.00")

        # February: available stays $400 (no spending), funded resets
        february_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),  # Reset for new month
            available_now=Decimal("400.00"),  # Still $400
            current_month=date(2026, 2, 1),
        )
        assert february_underfunded == Decimal("600.00")  # Same underfunded

    def test_target_balance_decreases_as_available_grows(self) -> None:
        """Test underfunded decreases as available balance grows."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
            target_date=None,
        )

        # January: $400 available
        jan_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("400.00"),
            available_now=Decimal("400.00"),
            current_month=date(2026, 1, 1),
        )
        assert jan_underfunded == Decimal("600.00")

        # February: Add $300 more, now $700 available
        feb_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("300.00"),
            available_now=Decimal("700.00"),
            current_month=date(2026, 2, 1),
        )
        assert feb_underfunded == Decimal("300.00")

        # March: Add $300 more, now $1000 available - target met!
        mar_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("300.00"),
            available_now=Decimal("1000.00"),
            current_month=date(2026, 3, 1),
        )
        assert mar_underfunded == Decimal("0")

    def test_target_balance_with_overfunding(self) -> None:
        """Test target balance when available exceeds target."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
            target_date=None,
        )

        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("100.00"),
            available_now=Decimal("1500.00"),  # Over target
            current_month=date(2026, 1, 1),
        )

        assert underfunded == Decimal("0")


class TestTargetByDateRollover:
    """Tests for TARGET_BY_DATE target month rollover (T159).

    Target by Date targets:
    - months_left = months between current and target_date (inclusive)
    - needed_now = max(0, target_amount - available_now)
    - suggested_monthly = needed_now / months_left (ceiling)
    - Underfunded = max(0, suggested_monthly - funded_this_month)

    When month rolls over:
    - months_left decreases by 1
    - suggested_monthly increases (same amount over fewer months)
    """

    def test_target_by_date_months_left_calculation(self) -> None:
        """Test months_left calculation is correct."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 12, 1),  # December 2026
        )

        # January 2026: 12 months left
        assert target._calculate_months_left(date(2026, 1, 1)) == 12

        # June 2026: 7 months left
        assert target._calculate_months_left(date(2026, 6, 1)) == 7

        # December 2026: 1 month left
        assert target._calculate_months_left(date(2026, 12, 1)) == 1

    def test_target_by_date_suggested_monthly_increases_as_months_pass(self) -> None:
        """Test that suggested monthly amount increases as deadline approaches."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 12, 1),
        )

        # January: 12 months left, $0 available
        # Suggested = 1200 / 12 = $100/month
        jan_suggested = target.get_suggested_monthly(
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        assert jan_suggested == Decimal("100.00")

        # July: 6 months left, still $0 available
        # Suggested = 1200 / 6 = $200/month
        jul_suggested = target.get_suggested_monthly(
            available_now=Decimal("0.00"),
            current_month=date(2026, 7, 1),
        )
        assert jul_suggested == Decimal("200.00")

    def test_target_by_date_suggested_monthly_adjusts_with_available(self) -> None:
        """Test that suggested monthly adjusts based on current available."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 12, 1),
        )

        # January: 12 months, $600 already saved
        # needed_now = 1200 - 600 = 600
        # Suggested = 600 / 12 = $50/month
        jan_suggested = target.get_suggested_monthly(
            available_now=Decimal("600.00"),
            current_month=date(2026, 1, 1),
        )
        assert jan_suggested == Decimal("50.00")

    def test_target_by_date_underfunded_rollover(self) -> None:
        """Test underfunded calculation across months."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 6, 1),  # June 2026
        )

        # January: 6 months left, $0 available
        # Suggested = 1200 / 6 = $200/month
        jan_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        assert jan_underfunded == Decimal("200.00")

        # February: 5 months left, $200 available (funded in Jan)
        # needed_now = 1200 - 200 = 1000
        # Suggested = 1000 / 5 = $200/month
        feb_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("200.00"),
            current_month=date(2026, 2, 1),
        )
        assert feb_underfunded == Decimal("200.00")

        # If we fall behind: February with $0 available (spent it)
        # needed_now = 1200 - 0 = 1200
        # Suggested = 1200 / 5 = $240/month
        feb_behind_underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 2, 1),
        )
        assert feb_behind_underfunded == Decimal("240.00")

    def test_target_by_date_partial_funding_reduces_underfunded(self) -> None:
        """Test that partial funding reduces underfunded amount."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 6, 1),
        )

        # January: 6 months, $0 available, $100 funded so far this month
        # Suggested = $200/month
        # Underfunded = 200 - 100 = $100
        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("100.00"),
            available_now=Decimal("100.00"),
            current_month=date(2026, 1, 1),
        )
        # Actually need to recalculate:
        # needed_now = 1200 - 100 = 1100
        # suggested = 1100 / 6 = 183.34 (ceiling)
        # underfunded = 183.34 - 100 = 83.34
        expected = Decimal("83.34")
        assert underfunded == expected

    def test_target_by_date_target_met_early(self) -> None:
        """Test that underfunded is zero when target is already met."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 6, 1),
        )

        # Already have $1200, target met
        underfunded = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("1200.00"),
            current_month=date(2026, 3, 1),
        )
        assert underfunded == Decimal("0")

    def test_target_by_date_minimum_one_month(self) -> None:
        """Test that months_left never goes below 1."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 1, 1),  # Target date in past
        )

        # Past the target date - should still work with 1 month
        months = target._calculate_months_left(date(2026, 3, 1))
        assert months == 1  # Minimum 1 to avoid division by zero


class TestMonthBoundaryBehavior:
    """Tests for behavior at month boundaries."""

    def test_all_target_types_at_month_boundary(self) -> None:
        """Test all target types behavior when crossing month boundary."""
        user_id = uuid4()

        # Monthly Needed: resets each month
        monthly_target = CategoryTarget(
            id=uuid4(),
            user_id=user_id,
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        # Target Balance: persists
        balance_target = CategoryTarget(
            id=uuid4(),
            user_id=user_id,
            category_id=uuid4(),
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("500.00"),
            target_date=None,
        )

        # Target by Date: adjusts suggestion
        date_target = CategoryTarget(
            id=uuid4(),
            user_id=user_id,
            category_id=uuid4(),
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("600.00"),
            target_date=date(2026, 6, 1),
        )

        # End of January: all fully funded for the month
        jan_monthly = monthly_target.calculate_underfunded(
            funded_this_month=Decimal("200.00"),
            available_now=Decimal("200.00"),
            current_month=date(2026, 1, 1),
        )
        jan_balance = balance_target.calculate_underfunded(
            funded_this_month=Decimal("200.00"),
            available_now=Decimal("200.00"),
            current_month=date(2026, 1, 1),
        )
        jan_date = date_target.calculate_underfunded(
            funded_this_month=Decimal("100.00"),  # Suggested = 600/6 = 100
            available_now=Decimal("100.00"),
            current_month=date(2026, 1, 1),
        )

        assert jan_monthly == Decimal("0")  # Fully funded for January
        assert jan_balance == Decimal("300.00")  # Still need $300 more
        assert jan_date == Decimal("0")  # Funded suggested amount

        # Start of February: funded_this_month resets
        feb_monthly = monthly_target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),  # Reset!
            available_now=Decimal("200.00"),  # Carried over
            current_month=date(2026, 2, 1),
        )
        feb_balance = balance_target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),  # Reset
            available_now=Decimal("200.00"),  # Same as before
            current_month=date(2026, 2, 1),
        )
        feb_date = date_target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),  # Reset!
            available_now=Decimal("100.00"),  # Same
            current_month=date(2026, 2, 1),
        )

        assert feb_monthly == Decimal("200.00")  # Need to fund again!
        assert feb_balance == Decimal("300.00")  # Still need $300
        # Feb: needed = 600 - 100 = 500, months = 5
        # Suggested = 500 / 5 = 100
        assert feb_date == Decimal("100.00")


class TestSuggestedMonthlyForNonDateTargets:
    """Test suggested monthly returns None for non-date targets."""

    def test_monthly_needed_returns_none(self) -> None:
        """Test get_suggested_monthly returns None for MONTHLY_NEEDED."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        result = target.get_suggested_monthly(
            available_now=Decimal("100.00"),
            current_month=date(2026, 1, 1),
        )
        assert result is None

    def test_target_balance_returns_none(self) -> None:
        """Test get_suggested_monthly returns None for TARGET_BALANCE."""
        target = CategoryTarget(
            id=uuid4(),
            user_id=uuid4(),
            category_id=uuid4(),
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("500.00"),
            target_date=None,
        )

        result = target.get_suggested_monthly(
            available_now=Decimal("200.00"),
            current_month=date(2026, 1, 1),
        )
        assert result is None


# =============================================================================
# TargetService unit tests - testing service methods with mocked database
# =============================================================================

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mybudget.models.category import Category
from mybudget.schemas.target import CategoryTargetCreate, CategoryTargetUpdate
from mybudget.services.target_service import TargetService


class TestTargetServiceInit:
    """Tests for TargetService initialization."""

    def test_init_with_db_session(self) -> None:
        """Test TargetService can be initialized with db session."""
        mock_db = MagicMock()
        service = TargetService(mock_db)
        assert service.db == mock_db
        assert service.budget_service is not None


class TestCreateTarget:
    """Tests for create_target method."""

    @pytest.mark.asyncio
    async def test_create_target_monthly_needed_success(self) -> None:
        """Test creating a MONTHLY_NEEDED target successfully."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        data = CategoryTargetCreate(
            category_id=category_id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        mock_category = Category(
            id=category_id,
            user_id=user_id,
            name="Test Category",
        )

        # Mock _get_category to return the category
        with patch.object(service, "_get_category", new_callable=AsyncMock) as mock_get_cat:
            mock_get_cat.return_value = mock_category

            # Mock get_target_by_category to return None (no existing target)
            with patch.object(
                service, "get_target_by_category", new_callable=AsyncMock
            ) as mock_get_target:
                mock_get_target.return_value = None

                mock_db.add = MagicMock()
                mock_db.commit = AsyncMock()
                mock_db.refresh = AsyncMock()

                result = await service.create_target(user_id, data)

                assert result is not None
                mock_db.add.assert_called_once()
                added_target = mock_db.add.call_args[0][0]
                assert isinstance(added_target, CategoryTarget)
                assert added_target.user_id == user_id
                assert added_target.category_id == category_id
                assert added_target.target_type == TargetType.MONTHLY_NEEDED
                assert added_target.amount == Decimal("200.00")
                mock_db.commit.assert_awaited_once()
                mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_target_by_date_success(self) -> None:
        """Test creating a TARGET_BY_DATE target successfully."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        target_date = date(2026, 12, 1)
        data = CategoryTargetCreate(
            category_id=category_id,
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=target_date,
        )

        mock_category = Category(id=category_id, user_id=user_id, name="Vacation Fund")

        with patch.object(service, "_get_category", new_callable=AsyncMock) as mock_get_cat:
            mock_get_cat.return_value = mock_category
            with patch.object(
                service, "get_target_by_category", new_callable=AsyncMock
            ) as mock_get_target:
                mock_get_target.return_value = None

                mock_db.add = MagicMock()
                mock_db.commit = AsyncMock()
                mock_db.refresh = AsyncMock()

                result = await service.create_target(user_id, data)

                assert result is not None
                added_target = mock_db.add.call_args[0][0]
                assert added_target.target_type == TargetType.TARGET_BY_DATE
                assert added_target.target_date == target_date
                assert added_target.amount == Decimal("1200.00")

    @pytest.mark.asyncio
    async def test_create_target_category_not_found(self) -> None:
        """Test creating a target returns None when category doesn't exist."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        data = CategoryTargetCreate(
            category_id=category_id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        with patch.object(service, "_get_category", new_callable=AsyncMock) as mock_get_cat:
            mock_get_cat.return_value = None

            result = await service.create_target(user_id, data)

            assert result is None
            mock_get_cat.assert_awaited_once_with(user_id, category_id)

    @pytest.mark.asyncio
    async def test_create_target_already_exists_raises_error(self) -> None:
        """Test creating a target raises ValueError when category already has target."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        data = CategoryTargetCreate(
            category_id=category_id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        mock_category = Category(id=category_id, user_id=user_id, name="Test Category")
        existing_target = CategoryTarget(
            id=uuid4(),
            user_id=user_id,
            category_id=category_id,
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("500.00"),
        )

        with patch.object(service, "_get_category", new_callable=AsyncMock) as mock_get_cat:
            mock_get_cat.return_value = mock_category
            with patch.object(
                service, "get_target_by_category", new_callable=AsyncMock
            ) as mock_get_target:
                mock_get_target.return_value = existing_target

                with pytest.raises(ValueError, match="Category already has a target"):
                    await service.create_target(user_id, data)


class TestGetTarget:
    """Tests for get_target method."""

    @pytest.mark.asyncio
    async def test_get_target_found(self) -> None:
        """Test getting a target that exists and belongs to user."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = CategoryTarget(
            id=target_id,
            user_id=user_id,
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_target
        mock_db.execute.return_value = mock_result

        result = await service.get_target(user_id, target_id)

        assert result == mock_target
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_target_not_found(self) -> None:
        """Test getting a target that doesn't exist."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_target(user_id, target_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_target_wrong_user(self) -> None:
        """Test that getting a target with wrong user_id returns None."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        other_user_id = uuid4()
        target_id = uuid4()

        # Query returns None because user_id doesn't match
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_target(other_user_id, target_id)

        assert result is None


class TestGetTargetByCategory:
    """Tests for get_target_by_category method."""

    @pytest.mark.asyncio
    async def test_get_target_by_category_found(self) -> None:
        """Test getting a target by category ID."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_target = CategoryTarget(
            id=uuid4(),
            user_id=user_id,
            category_id=category_id,
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_target
        mock_db.execute.return_value = mock_result

        result = await service.get_target_by_category(user_id, category_id)

        assert result == mock_target

    @pytest.mark.asyncio
    async def test_get_target_by_category_not_found(self) -> None:
        """Test getting target by category returns None when not found."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_target_by_category(user_id, category_id)

        assert result is None


class TestListTargets:
    """Tests for list_targets method."""

    @pytest.mark.asyncio
    async def test_list_targets_with_targets(self) -> None:
        """Test listing targets for a user with multiple targets."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()

        mock_targets = [
            CategoryTarget(
                id=uuid4(),
                user_id=user_id,
                category_id=uuid4(),
                target_type=TargetType.MONTHLY_NEEDED,
                amount=Decimal("100.00"),
            ),
            CategoryTarget(
                id=uuid4(),
                user_id=user_id,
                category_id=uuid4(),
                target_type=TargetType.TARGET_BALANCE,
                amount=Decimal("500.00"),
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_targets
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_targets(user_id)

        assert len(result) == 2
        assert result == mock_targets

    @pytest.mark.asyncio
    async def test_list_targets_empty(self) -> None:
        """Test listing targets for a user with no targets."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_targets(user_id)

        assert result == []


class TestUpdateTarget:
    """Tests for update_target method."""

    @pytest.mark.asyncio
    async def test_update_target_amount_success(self) -> None:
        """Test updating target amount successfully."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = MagicMock()
        mock_target.target_type = TargetType.MONTHLY_NEEDED
        mock_target.amount = Decimal("200.00")
        mock_target.target_date = None

        data = CategoryTargetUpdate(amount=Decimal("300.00"))

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_target(user_id, target_id, data)

            assert result is not None
            assert mock_target.amount == Decimal("300.00")
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_target_type_change(self) -> None:
        """Test changing target type."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = MagicMock()
        mock_target.target_type = TargetType.MONTHLY_NEEDED
        mock_target.amount = Decimal("200.00")
        mock_target.target_date = None

        data = CategoryTargetUpdate(target_type=TargetType.TARGET_BALANCE)

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_target(user_id, target_id, data)

            assert result is not None
            assert mock_target.target_type == TargetType.TARGET_BALANCE

    @pytest.mark.asyncio
    async def test_update_target_not_found(self) -> None:
        """Test updating a target that doesn't exist."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()
        data = CategoryTargetUpdate(amount=Decimal("300.00"))

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.update_target(user_id, target_id, data)

            assert result is None

    @pytest.mark.asyncio
    async def test_update_target_to_date_type_without_date_raises(self) -> None:
        """Test updating to TARGET_BY_DATE without target_date raises error."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = MagicMock()
        mock_target.target_type = TargetType.MONTHLY_NEEDED
        mock_target.amount = Decimal("200.00")
        mock_target.target_date = None

        data = CategoryTargetUpdate(target_type=TargetType.TARGET_BY_DATE)

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target

            with pytest.raises(ValueError, match="target_date is required"):
                await service.update_target(user_id, target_id, data)

    @pytest.mark.asyncio
    async def test_update_target_clears_date_for_non_date_type(self) -> None:
        """Test updating from TARGET_BY_DATE to other type clears target_date."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = MagicMock()
        mock_target.target_type = TargetType.TARGET_BY_DATE
        mock_target.amount = Decimal("1200.00")
        mock_target.target_date = date(2026, 12, 1)

        data = CategoryTargetUpdate(target_type=TargetType.MONTHLY_NEEDED)

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_target(user_id, target_id, data)

            assert result is not None
            assert mock_target.target_type == TargetType.MONTHLY_NEEDED
            # target_date should be cleared
            assert mock_target.target_date is None

    @pytest.mark.asyncio
    async def test_update_target_no_changes(self) -> None:
        """Test updating target with None values (no changes)."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = MagicMock()
        mock_target.target_type = TargetType.MONTHLY_NEEDED
        mock_target.amount = Decimal("200.00")
        mock_target.target_date = None

        data = CategoryTargetUpdate()

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_target(user_id, target_id, data)

            assert result is not None
            # Values unchanged
            assert mock_target.amount == Decimal("200.00")
            assert mock_target.target_type == TargetType.MONTHLY_NEEDED

    @pytest.mark.asyncio
    async def test_update_target_date_change(self) -> None:
        """Test updating target_date for TARGET_BY_DATE target."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = MagicMock()
        mock_target.target_type = TargetType.TARGET_BY_DATE
        mock_target.amount = Decimal("1200.00")
        mock_target.target_date = date(2026, 6, 1)

        new_date = date(2026, 12, 1)
        data = CategoryTargetUpdate(target_date=new_date)

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_target(user_id, target_id, data)

            assert result is not None
            assert mock_target.target_date == new_date


class TestDeleteTarget:
    """Tests for delete_target method."""

    @pytest.mark.asyncio
    async def test_delete_target_success(self) -> None:
        """Test deleting a target successfully."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        mock_target = CategoryTarget(
            id=target_id,
            user_id=user_id,
            category_id=uuid4(),
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
        )

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()

            result = await service.delete_target(user_id, target_id)

            assert result is True
            mock_db.delete.assert_awaited_once_with(mock_target)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_target_not_found(self) -> None:
        """Test deleting a target that doesn't exist."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.delete_target(user_id, target_id)

            assert result is False


class TestCalculateUnderfunded:
    """Tests for calculate_underfunded service method."""

    @pytest.mark.asyncio
    async def test_calculate_underfunded_target_not_found(self) -> None:
        """Test calculate_underfunded returns None when target not found."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()
        month = date(2026, 1, 1)

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.calculate_underfunded(user_id, target_id, month)

            assert result is None

    @pytest.mark.asyncio
    async def test_calculate_underfunded_monthly_needed(self) -> None:
        """Test calculate_underfunded for MONTHLY_NEEDED target."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 15)

        mock_target = CategoryTarget(
            id=target_id,
            user_id=user_id,
            category_id=category_id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target

            # Mock budget service methods
            with patch.object(
                service.budget_service, "get_funded_this_month", new_callable=AsyncMock
            ) as mock_funded:
                mock_funded.return_value = Decimal("75.00")

                with patch.object(
                    service.budget_service, "get_available", new_callable=AsyncMock
                ) as mock_available:
                    mock_available.return_value = Decimal("100.00")

                    result = await service.calculate_underfunded(
                        user_id, target_id, month
                    )

                    assert result is not None
                    assert result["target_id"] == target_id
                    assert result["category_id"] == category_id
                    assert result["month"] == date(2026, 1, 1)  # First day
                    assert result["target_type"] == TargetType.MONTHLY_NEEDED
                    assert result["target_amount"] == "200.00"
                    assert result["funded_this_month"] == "75.00"
                    assert result["available_now"] == "100.00"
                    assert result["underfunded"] == "125.00"  # 200 - 75
                    assert result["status"] == "UNDERFUNDED"

    @pytest.mark.asyncio
    async def test_calculate_underfunded_funded_status(self) -> None:
        """Test calculate_underfunded returns FUNDED status when target met."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        mock_target = CategoryTarget(
            id=target_id,
            user_id=user_id,
            category_id=category_id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            with patch.object(
                service.budget_service, "get_funded_this_month", new_callable=AsyncMock
            ) as mock_funded:
                mock_funded.return_value = Decimal("200.00")
                with patch.object(
                    service.budget_service, "get_available", new_callable=AsyncMock
                ) as mock_available:
                    mock_available.return_value = Decimal("200.00")

                    result = await service.calculate_underfunded(
                        user_id, target_id, month
                    )

                    assert result["underfunded"] == "0.00"
                    assert result["status"] == "FUNDED"

    @pytest.mark.asyncio
    async def test_calculate_underfunded_overfunded_status(self) -> None:
        """Test calculate_underfunded returns OVERFUNDED status for MONTHLY_NEEDED."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        mock_target = CategoryTarget(
            id=target_id,
            user_id=user_id,
            category_id=category_id,
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("200.00"),
            target_date=None,
        )

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            with patch.object(
                service.budget_service, "get_funded_this_month", new_callable=AsyncMock
            ) as mock_funded:
                mock_funded.return_value = Decimal("250.00")  # Over target
                with patch.object(
                    service.budget_service, "get_available", new_callable=AsyncMock
                ) as mock_available:
                    mock_available.return_value = Decimal("250.00")

                    result = await service.calculate_underfunded(
                        user_id, target_id, month
                    )

                    assert result["underfunded"] == "0.00"
                    assert result["status"] == "OVERFUNDED"

    @pytest.mark.asyncio
    async def test_calculate_underfunded_target_by_date(self) -> None:
        """Test calculate_underfunded for TARGET_BY_DATE includes extra fields."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        target_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        mock_target = CategoryTarget(
            id=target_id,
            user_id=user_id,
            category_id=category_id,
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 12, 1),
        )

        with patch.object(service, "get_target", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_target
            with patch.object(
                service.budget_service, "get_funded_this_month", new_callable=AsyncMock
            ) as mock_funded:
                mock_funded.return_value = Decimal("0.00")
                with patch.object(
                    service.budget_service, "get_available", new_callable=AsyncMock
                ) as mock_available:
                    mock_available.return_value = Decimal("0.00")

                    result = await service.calculate_underfunded(
                        user_id, target_id, month
                    )

                    assert result["target_type"] == TargetType.TARGET_BY_DATE
                    assert "months_left" in result
                    assert result["months_left"] == 12
                    assert "suggested_monthly" in result
                    assert result["suggested_monthly"] == "100.00"


class TestGetCategoryName:
    """Tests for get_category_name method."""

    @pytest.mark.asyncio
    async def test_get_category_name_found(self) -> None:
        """Test getting category name when category exists."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_category = Category(id=category_id, user_id=user_id, name="Groceries")

        with patch.object(service, "_get_category", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_category

            result = await service.get_category_name(user_id, category_id)

            assert result == "Groceries"

    @pytest.mark.asyncio
    async def test_get_category_name_not_found(self) -> None:
        """Test getting category name returns None when not found."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        with patch.object(service, "_get_category", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.get_category_name(user_id, category_id)

            assert result is None


class TestGetCategoryInternal:
    """Tests for _get_category internal method."""

    @pytest.mark.asyncio
    async def test_get_category_found(self) -> None:
        """Test _get_category returns category when found."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_category = Category(id=category_id, user_id=user_id, name="Test")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_category
        mock_db.execute.return_value = mock_result

        result = await service._get_category(user_id, category_id)

        assert result == mock_category

    @pytest.mark.asyncio
    async def test_get_category_not_found(self) -> None:
        """Test _get_category returns None when not found."""
        mock_db = AsyncMock()
        service = TargetService(mock_db)

        user_id = uuid4()
        category_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service._get_category(user_id, category_id)

        assert result is None
