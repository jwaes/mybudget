"""
Unit tests for target service - month rollover behavior.

Tests how targets behave when navigating between months.
Covers User Story 6 - Month Rollover.
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

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
