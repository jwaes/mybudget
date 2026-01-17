"""
Decimal utility functions for MyBudget.

Provides utilities for working with Decimal values for precise financial
calculations. All monetary values should use Decimal to avoid floating-point
precision errors.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def safe_decimal(value: str | int | float | Decimal) -> Decimal:
    """Convert a value to Decimal safely.

    Args:
        value: A string, int, float, or Decimal to convert.

    Returns:
        A Decimal representation of the value.

    Raises:
        ValueError: If the value cannot be converted to Decimal.
    """
    if isinstance(value, Decimal):
        return value

    try:
        if isinstance(value, float):
            # Convert float to string first to avoid precision issues
            return Decimal(str(value))
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError(f"Cannot convert {value!r} to Decimal: {e}") from e


def round_currency(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to the specified number of decimal places.

    Uses ROUND_HALF_UP rounding (standard financial rounding).

    Args:
        value: The Decimal value to round.
        places: Number of decimal places (default 2 for currency).

    Returns:
        The rounded Decimal value.
    """
    quantize_str = "0." + "0" * places
    return value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


def format_currency(value: Decimal, symbol: str = "€") -> str:
    """Format a Decimal value as a currency string.

    Args:
        value: The Decimal value to format.
        symbol: The currency symbol (default €).

    Returns:
        A formatted currency string (e.g., "€1,234.56").
    """
    rounded = round_currency(value)
    # Format with thousands separator and 2 decimal places
    formatted = f"{rounded:,.2f}"
    return f"{symbol}{formatted}"


def sum_decimals(*values: Decimal) -> Decimal:
    """Sum multiple Decimal values.

    Args:
        *values: Decimal values to sum.

    Returns:
        The sum of all values, or Decimal("0") if no values provided.
    """
    if not values:
        return Decimal("0")
    return sum(values, start=Decimal("0"))


def is_positive(value: Decimal) -> bool:
    """Check if a Decimal value is positive (greater than zero).

    Args:
        value: The Decimal value to check.

    Returns:
        True if value > 0, False otherwise.
    """
    return value > Decimal("0")


def is_negative(value: Decimal) -> bool:
    """Check if a Decimal value is negative (less than zero).

    Args:
        value: The Decimal value to check.

    Returns:
        True if value < 0, False otherwise.
    """
    return value < Decimal("0")


def is_zero(value: Decimal) -> bool:
    """Check if a Decimal value is zero.

    Args:
        value: The Decimal value to check.

    Returns:
        True if value == 0, False otherwise.
    """
    return value == Decimal("0")
