"""
Unit tests for decimal utilities.
"""
from decimal import Decimal

import pytest

from mybudget.lib.decimal_utils import (
    format_currency,
    is_negative,
    is_positive,
    is_zero,
    round_currency,
    safe_decimal,
    sum_decimals,
)


@pytest.mark.unit
class TestDecimalUtils:
    """Tests for decimal utility functions."""

    def test_safe_decimal_from_string(self) -> None:
        """Test converting string to Decimal."""
        result = safe_decimal("123.45")
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

    def test_safe_decimal_from_int(self) -> None:
        """Test converting int to Decimal."""
        result = safe_decimal(100)
        assert result == Decimal("100")

    def test_safe_decimal_from_float(self) -> None:
        """Test converting float to Decimal."""
        result = safe_decimal(123.45)
        assert result == Decimal("123.45")

    def test_safe_decimal_from_decimal(self) -> None:
        """Test that Decimal passes through unchanged."""
        original = Decimal("123.45")
        result = safe_decimal(original)
        assert result == original
        assert result is original

    def test_safe_decimal_invalid_string(self) -> None:
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Cannot convert"):
            safe_decimal("not a number")

    def test_round_currency_default(self) -> None:
        """Test rounding to 2 decimal places (default)."""
        result = round_currency(Decimal("123.456"))
        assert result == Decimal("123.46")

    def test_round_currency_down(self) -> None:
        """Test rounding down."""
        result = round_currency(Decimal("123.444"))
        assert result == Decimal("123.44")

    def test_round_currency_half_up(self) -> None:
        """Test rounding .5 up (ROUND_HALF_UP)."""
        result = round_currency(Decimal("123.445"))
        assert result == Decimal("123.45")

    def test_round_currency_custom_places(self) -> None:
        """Test rounding to custom number of places."""
        result = round_currency(Decimal("123.4567"), places=3)
        assert result == Decimal("123.457")

    def test_round_currency_already_rounded(self) -> None:
        """Test that already rounded values stay the same."""
        result = round_currency(Decimal("123.45"))
        assert result == Decimal("123.45")

    def test_format_currency_positive(self) -> None:
        """Test formatting positive currency."""
        result = format_currency(Decimal("1234.56"))
        assert result == "€1,234.56"

    def test_format_currency_negative(self) -> None:
        """Test formatting negative currency."""
        result = format_currency(Decimal("-50.00"))
        assert result == "€-50.00"

    def test_format_currency_custom_symbol(self) -> None:
        """Test formatting with custom currency symbol."""
        result = format_currency(Decimal("100.00"), "$")
        assert result == "$100.00"

    def test_format_currency_large_number(self) -> None:
        """Test formatting large numbers with thousands separators."""
        result = format_currency(Decimal("1234567.89"))
        assert result == "€1,234,567.89"

    def test_format_currency_zero(self) -> None:
        """Test formatting zero."""
        result = format_currency(Decimal("0"))
        assert result == "€0.00"

    def test_sum_decimals_multiple(self) -> None:
        """Test summing multiple decimals."""
        result = sum_decimals(
            Decimal("10.50"), Decimal("20.25"), Decimal("5.00")
        )
        assert result == Decimal("35.75")

    def test_sum_decimals_single(self) -> None:
        """Test summing single decimal."""
        result = sum_decimals(Decimal("10.50"))
        assert result == Decimal("10.50")

    def test_sum_decimals_empty(self) -> None:
        """Test summing no decimals returns zero."""
        result = sum_decimals()
        assert result == Decimal("0")

    def test_sum_decimals_with_negatives(self) -> None:
        """Test summing with negative values."""
        result = sum_decimals(
            Decimal("100.00"), Decimal("-30.00"), Decimal("20.00")
        )
        assert result == Decimal("90.00")

    def test_is_positive_true(self) -> None:
        """Test is_positive returns True for positive values."""
        assert is_positive(Decimal("10.00")) is True
        assert is_positive(Decimal("0.01")) is True

    def test_is_positive_false(self) -> None:
        """Test is_positive returns False for zero and negative."""
        assert is_positive(Decimal("0")) is False
        assert is_positive(Decimal("-10.00")) is False

    def test_is_negative_true(self) -> None:
        """Test is_negative returns True for negative values."""
        assert is_negative(Decimal("-10.00")) is True
        assert is_negative(Decimal("-0.01")) is True

    def test_is_negative_false(self) -> None:
        """Test is_negative returns False for zero and positive."""
        assert is_negative(Decimal("0")) is False
        assert is_negative(Decimal("10.00")) is False

    def test_is_zero_true(self) -> None:
        """Test is_zero returns True for zero."""
        assert is_zero(Decimal("0")) is True
        assert is_zero(Decimal("0.00")) is True

    def test_is_zero_false(self) -> None:
        """Test is_zero returns False for non-zero."""
        assert is_zero(Decimal("0.01")) is False
        assert is_zero(Decimal("-0.01")) is False
        assert is_zero(Decimal("10.00")) is False

    def test_decimal_precision(self) -> None:
        """Test that Decimal maintains precision unlike float."""
        # This would fail with float arithmetic
        result = sum_decimals(Decimal("0.1"), Decimal("0.2"))
        assert result == Decimal("0.3")  # Exactly 0.3, not 0.30000000000000004
