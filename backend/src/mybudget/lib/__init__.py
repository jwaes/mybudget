"""
Library utilities for MyBudget.

Provides common utility functions for date handling, decimal operations,
authentication, and custom exceptions.
"""

from mybudget.lib.auth import hash_password, verify_password
from mybudget.lib.date_utils import (
    add_months,
    calculate_months_between,
    get_current_month,
    get_month_boundaries,
    get_month_first_day,
)
from mybudget.lib.decimal_utils import (
    format_currency,
    is_negative,
    is_positive,
    is_zero,
    round_currency,
    safe_decimal,
    sum_decimals,
)
from mybudget.lib.exceptions import (
    AccountNotFoundError,
    AuthenticationError,
    AuthorizationError,
    CategoryNotFoundError,
    InsufficientFundsError,
    InvalidTargetDateError,
    MyBudgetError,
    ReconciliationError,
    TransactionNotFoundError,
)

__all__ = [
    # Auth
    "hash_password",
    "verify_password",
    # Date utilities
    "get_month_first_day",
    "get_month_boundaries",
    "calculate_months_between",
    "get_current_month",
    "add_months",
    # Decimal utilities
    "safe_decimal",
    "round_currency",
    "format_currency",
    "sum_decimals",
    "is_positive",
    "is_negative",
    "is_zero",
    # Exceptions
    "MyBudgetError",
    "InsufficientFundsError",
    "InvalidTargetDateError",
    "ReconciliationError",
    "CategoryNotFoundError",
    "AccountNotFoundError",
    "TransactionNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
]
