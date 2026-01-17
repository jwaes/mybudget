"""
Date utility functions for MyBudget.

Provides utilities for working with dates, particularly for month-based
budget calculations.
"""

from calendar import monthrange
from datetime import date, datetime


def get_month_first_day(dt: date | datetime) -> date:
    """Get the first day of the month for a given date or datetime.

    Args:
        dt: A date or datetime object.

    Returns:
        A date object representing the first day of the month.
    """
    if isinstance(dt, datetime):
        return date(dt.year, dt.month, 1)
    return date(dt.year, dt.month, 1)


def get_month_boundaries(dt: date | datetime) -> tuple[date, date]:
    """Get the first and last day of the month for a given date.

    Args:
        dt: A date or datetime object.

    Returns:
        A tuple of (first_day, last_day) as date objects.
    """
    if isinstance(dt, datetime):
        dt = dt.date()

    first_day = date(dt.year, dt.month, 1)
    _, last_day_num = monthrange(dt.year, dt.month)
    last_day = date(dt.year, dt.month, last_day_num)

    return first_day, last_day


def calculate_months_between(start: date, end: date) -> int:
    """Calculate the number of months between two dates.

    Counts from the start month to the end month. If start is mid-month,
    includes that month in the count.

    Args:
        start: The start date.
        end: The end date.

    Returns:
        Number of months between the dates (0 if same month, negative if end before start).
    """
    if end < start:
        return 0

    # Calculate month difference
    months = (end.year - start.year) * 12 + (end.month - start.month)

    # If start is not the first day of month, add 1 to include partial month
    if start.day > 1:
        months += 1

    return months


def get_current_month() -> date:
    """Get the first day of the current month.

    Returns:
        A date object representing the first day of the current month.
    """
    today = date.today()
    return date(today.year, today.month, 1)


def add_months(dt: date, months: int) -> date:
    """Add (or subtract) months to/from a date.

    If the resulting day doesn't exist in the target month (e.g., Jan 31 + 1 month),
    returns the last day of the target month.

    Args:
        dt: The starting date.
        months: Number of months to add (can be negative).

    Returns:
        The resulting date.
    """
    if months == 0:
        return dt

    # Calculate target year and month
    total_months = dt.year * 12 + dt.month - 1 + months
    target_year = total_months // 12
    target_month = total_months % 12 + 1

    # Handle day overflow (e.g., Jan 31 + 1 month = Feb 28)
    _, max_day = monthrange(target_year, target_month)
    target_day = min(dt.day, max_day)

    return date(target_year, target_month, target_day)
