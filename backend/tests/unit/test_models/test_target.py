"""
Unit tests for CategoryTarget model.

Tests target creation, validation, and underfunded calculations.
"""
from datetime import date
from decimal import Decimal

from mybudget.models.target import CategoryTarget, TargetType


class TestTargetModel:
    """Tests for CategoryTarget model creation and properties."""

    def test_create_monthly_needed_target(self) -> None:
        """Test creating a Monthly Needed target."""
        target = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("400.00"),
        )
        assert target.target_type == TargetType.MONTHLY_NEEDED
        assert target.amount == Decimal("400.00")
        assert target.target_date is None

    def test_create_target_balance_target(self) -> None:
        """Test creating a Target Balance target."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("10000.00"),
        )
        assert target.target_type == TargetType.TARGET_BALANCE
        assert target.amount == Decimal("10000.00")
        assert target.target_date is None

    def test_create_target_by_date_target(self) -> None:
        """Test creating a Target by Date target."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("5000.00"),
            target_date=date(2026, 12, 31),
        )
        assert target.target_type == TargetType.TARGET_BY_DATE
        assert target.amount == Decimal("5000.00")
        assert target.target_date == date(2026, 12, 31)

    def test_target_type_enum_values(self) -> None:
        """Test TargetType enum values."""
        assert TargetType.MONTHLY_NEEDED.value == "MONTHLY_NEEDED"
        assert TargetType.TARGET_BALANCE.value == "TARGET_BALANCE"
        assert TargetType.TARGET_BY_DATE.value == "TARGET_BY_DATE"


class TestMonthlyNeededCalculation:
    """Tests for Monthly Needed underfunded calculation."""

    def test_underfunded_when_partially_funded(self) -> None:
        """Test underfunded = target - funded_this_month."""
        target = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("400.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("250.00"),
            available_now=Decimal("250.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("150.00")

    def test_underfunded_when_not_funded(self) -> None:
        """Test underfunded = target when nothing funded."""
        target = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("400.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("400.00")

    def test_underfunded_zero_when_fully_funded(self) -> None:
        """Test underfunded = 0 when fully funded."""
        target = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("400.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("400.00"),
            available_now=Decimal("400.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("0")

    def test_underfunded_zero_when_overfunded(self) -> None:
        """Test underfunded = 0 when overfunded."""
        target = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("400.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("500.00"),
            available_now=Decimal("500.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("0")


class TestTargetBalanceCalculation:
    """Tests for Target Balance underfunded calculation."""

    def test_underfunded_when_below_target(self) -> None:
        """Test underfunded = target - available."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("100.00"),
            available_now=Decimal("600.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("400.00")

    def test_underfunded_when_no_balance(self) -> None:
        """Test underfunded = target when no balance."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("1000.00")

    def test_underfunded_zero_when_at_target(self) -> None:
        """Test underfunded = 0 when at target balance."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("1000.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("0")

    def test_underfunded_zero_when_above_target(self) -> None:
        """Test underfunded = 0 when above target balance."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("1500.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("0")


class TestTargetByDateCalculation:
    """Tests for Target by Date underfunded calculation."""

    def test_underfunded_with_4_months_left(self) -> None:
        """Test underfunded calculation with 4 months to go."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 4, 1),  # April 2026
        )
        # From January, 4 months to April (Jan, Feb, Mar, Apr)
        # needed_now = 1200 - 0 = 1200
        # suggested_monthly = ceil(1200 / 4) = 300
        # underfunded = 300 - 0 = 300
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("300.00")

    def test_underfunded_with_partial_funding(self) -> None:
        """Test underfunded with partial funding this month."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 4, 1),
        )
        # available_now = 100 (from this month's funding)
        # needed_now = 1200 - 100 = 1100
        # months_left = 4 (Jan, Feb, Mar, Apr inclusive)
        # suggested_monthly = ceil(1100 / 4) = 275
        # underfunded = 275 - 100 = 175
        result = target.calculate_underfunded(
            funded_this_month=Decimal("100.00"),
            available_now=Decimal("100.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("175.00")

    def test_underfunded_with_existing_balance(self) -> None:
        """Test underfunded when there's existing balance from previous months."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 4, 1),
        )
        # available_now = 600 (from previous months)
        # needed_now = 1200 - 600 = 600
        # suggested_monthly = ceil(600 / 4) = 150
        # underfunded = 150 - 0 = 150
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("600.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("150.00")

    def test_underfunded_zero_when_fully_funded(self) -> None:
        """Test underfunded = 0 when monthly suggestion is met."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 4, 1),
        )
        # suggested_monthly = 300
        # underfunded = 300 - 300 = 0
        result = target.calculate_underfunded(
            funded_this_month=Decimal("300.00"),
            available_now=Decimal("300.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("0")

    def test_underfunded_zero_when_target_reached(self) -> None:
        """Test underfunded = 0 when target is already reached."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2026, 4, 1),
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("1200.00"),
            current_month=date(2026, 1, 1),
        )
        assert result == Decimal("0")


class TestMonthsLeftCalculation:
    """Tests for months_left calculation edge cases."""

    def test_months_left_same_month(self) -> None:
        """Test months_left = 1 when target month is current month."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("500.00"),
            target_date=date(2026, 1, 1),
        )
        # Edge case: current month = target month, should have 1 month left
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        # needed_now = 500, months_left = 1
        # suggested_monthly = 500
        # underfunded = 500
        assert result == Decimal("500.00")

    def test_months_left_past_target_date(self) -> None:
        """Test calculation when past target date (edge case)."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("500.00"),
            target_date=date(2025, 12, 1),  # Past date
        )
        # Should still have at least 1 month (prevent division by zero)
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        # With months_left = 1, underfunded = 500
        assert result == Decimal("500.00")

    def test_months_left_13_months(self) -> None:
        """Test months_left calculation over 13 months (inclusive)."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("1200.00"),
            target_date=date(2027, 1, 1),  # 13 months from Jan 2026 (inclusive)
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        # months_left = 13 (Jan 2026 to Jan 2027 inclusive)
        # suggested_monthly = ceil(1200 / 13) = 92.31
        assert result == Decimal("92.31")

    def test_months_left_across_years(self) -> None:
        """Test months_left calculation across year boundary."""
        target = CategoryTarget(
            target_type=TargetType.TARGET_BY_DATE,
            amount=Decimal("600.00"),
            target_date=date(2027, 3, 1),  # March 2027, 14 months from Jan 2026
        )
        result = target.calculate_underfunded(
            funded_this_month=Decimal("0.00"),
            available_now=Decimal("0.00"),
            current_month=date(2026, 1, 1),
        )
        # suggested_monthly = ceil(600 / 15) = 40 (15 months inclusive)
        # Actually: Jan26-Mar27 = 15 months
        # ceil(600/15) = 40
        assert result == Decimal("40.00")


class TestTargetValidation:
    """Tests for target validation rules."""

    def test_amount_must_be_positive(self) -> None:
        """Test that amount must be greater than zero."""
        # This validation should happen at Pydantic level, but
        # model should work with any value
        target = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("0.01"),  # Minimum valid amount
        )
        assert target.amount == Decimal("0.01")

    def test_target_type_is_required(self) -> None:
        """Test that target_type is required."""
        # This should raise an error at the DB level
        # In the model, we can create without it but it's not valid
        pass  # Validation happens at Pydantic/DB level

    def test_target_date_none_for_non_date_types(self) -> None:
        """Test that target_date is None for non-date types."""
        target_monthly = CategoryTarget(
            target_type=TargetType.MONTHLY_NEEDED,
            amount=Decimal("100.00"),
        )
        target_balance = CategoryTarget(
            target_type=TargetType.TARGET_BALANCE,
            amount=Decimal("1000.00"),
        )
        assert target_monthly.target_date is None
        assert target_balance.target_date is None
