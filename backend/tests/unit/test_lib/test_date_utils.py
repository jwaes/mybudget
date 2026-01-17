"""
Unit tests for date utilities.
"""
from datetime import UTC, date, datetime

import pytest

from mybudget.lib.date_utils import (
    add_months,
    calculate_months_between,
    get_current_month,
    get_month_boundaries,
    get_month_first_day,
)


@pytest.mark.unit
class TestDateUtils:
    """Tests for date utility functions."""

    def test_get_month_first_day_from_date(self) -> None:
        """Test getting first day from a date."""
        result = get_month_first_day(date(2026, 1, 16))
        assert result == date(2026, 1, 1)

    def test_get_month_first_day_from_datetime(self) -> None:
        """Test getting first day from a datetime."""
        dt = datetime(2026, 1, 16, 14, 30, 0, tzinfo=UTC)
        result = get_month_first_day(dt)
        assert result == date(2026, 1, 1)

    def test_get_month_first_day_already_first(self) -> None:
        """Test that first day returns itself."""
        result = get_month_first_day(date(2026, 1, 1))
        assert result == date(2026, 1, 1)

    def test_get_month_first_day_last_day(self) -> None:
        """Test getting first day from last day of month."""
        result = get_month_first_day(date(2026, 1, 31))
        assert result == date(2026, 1, 1)

    def test_get_month_boundaries_january(self) -> None:
        """Test month boundaries for January."""
        first, last = get_month_boundaries(date(2026, 1, 16))
        assert first == date(2026, 1, 1)
        assert last == date(2026, 1, 31)

    def test_get_month_boundaries_february_non_leap(self) -> None:
        """Test month boundaries for February in non-leap year."""
        first, last = get_month_boundaries(date(2026, 2, 15))
        assert first == date(2026, 2, 1)
        assert last == date(2026, 2, 28)

    def test_get_month_boundaries_february_leap(self) -> None:
        """Test month boundaries for February in leap year."""
        first, last = get_month_boundaries(date(2024, 2, 15))
        assert first == date(2024, 2, 1)
        assert last == date(2024, 2, 29)

    def test_get_month_boundaries_december(self) -> None:
        """Test month boundaries for December."""
        first, last = get_month_boundaries(date(2026, 12, 16))
        assert first == date(2026, 12, 1)
        assert last == date(2026, 12, 31)

    def test_calculate_months_between_same_month(self) -> None:
        """Test months between dates in same month."""
        result = calculate_months_between(date(2026, 1, 1), date(2026, 1, 31))
        assert result == 0

    def test_calculate_months_between_consecutive_months(self) -> None:
        """Test months between consecutive months."""
        result = calculate_months_between(date(2026, 1, 1), date(2026, 2, 1))
        assert result == 1

    def test_calculate_months_between_multiple_months(self) -> None:
        """Test months between multiple months apart."""
        result = calculate_months_between(date(2026, 1, 1), date(2026, 6, 1))
        assert result == 5

    def test_calculate_months_between_mid_month_start(self) -> None:
        """Test months counting from mid-month includes current month."""
        result = calculate_months_between(date(2026, 1, 15), date(2026, 6, 1))
        assert result == 6  # Includes January

    def test_calculate_months_between_mid_month_both(self) -> None:
        """Test months with both dates mid-month."""
        result = calculate_months_between(date(2026, 1, 15), date(2026, 6, 20))
        assert result == 6

    def test_calculate_months_between_across_year(self) -> None:
        """Test months between dates across year boundary."""
        result = calculate_months_between(date(2025, 10, 1), date(2026, 3, 1))
        assert result == 5

    def test_calculate_months_between_end_before_start(self) -> None:
        """Test that end before start returns 0."""
        result = calculate_months_between(date(2026, 6, 1), date(2026, 1, 1))
        assert result == 0

    def test_get_current_month(self) -> None:
        """Test getting current month returns first day."""
        result = get_current_month()
        # Should be first day of some month
        assert result.day == 1
        assert isinstance(result, date)

    def test_add_months_positive(self) -> None:
        """Test adding months."""
        result = add_months(date(2026, 1, 15), 3)
        assert result == date(2026, 4, 15)

    def test_add_months_negative(self) -> None:
        """Test subtracting months."""
        result = add_months(date(2026, 4, 15), -3)
        assert result == date(2026, 1, 15)

    def test_add_months_across_year(self) -> None:
        """Test adding months across year boundary."""
        result = add_months(date(2025, 11, 15), 3)
        assert result == date(2026, 2, 15)

    def test_add_months_end_of_month(self) -> None:
        """Test adding months when day doesn't exist in target month."""
        result = add_months(date(2026, 1, 31), 1)
        # January 31 + 1 month = February 28 (2026 is not a leap year)
        assert result == date(2026, 2, 28)

    def test_add_months_zero(self) -> None:
        """Test adding zero months returns same date."""
        original = date(2026, 1, 15)
        result = add_months(original, 0)
        assert result == original
