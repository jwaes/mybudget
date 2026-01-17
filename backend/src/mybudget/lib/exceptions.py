"""
Custom exceptions for MyBudget.

Provides domain-specific exception classes for clearer error handling.
"""


class MyBudgetError(Exception):
    """Base exception for all MyBudget-specific errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class InsufficientFundsError(MyBudgetError):
    """Raised when trying to assign more funds than available in To Assign."""

    def __init__(
        self, requested: str, available: str, message: str | None = None
    ) -> None:
        self.requested = requested
        self.available = available
        default_message = (
            f"Insufficient funds: requested {requested}, but only {available} available"
        )
        super().__init__(message or default_message)


class InvalidTargetDateError(MyBudgetError):
    """Raised when a target date is invalid (e.g., in the past)."""

    def __init__(self, target_date: str, message: str | None = None) -> None:
        self.target_date = target_date
        default_message = f"Target date {target_date} is invalid (cannot be in the past)"
        super().__init__(message or default_message)


class ReconciliationError(MyBudgetError):
    """Raised when a reconciliation operation fails."""

    def __init__(self, account_id: str, message: str | None = None) -> None:
        self.account_id = account_id
        default_message = f"Reconciliation error for account {account_id}"
        super().__init__(message or default_message)


class CategoryNotFoundError(MyBudgetError):
    """Raised when a category is not found."""

    def __init__(self, category_id: str, message: str | None = None) -> None:
        self.category_id = category_id
        default_message = f"Category {category_id} not found"
        super().__init__(message or default_message)


class AccountNotFoundError(MyBudgetError):
    """Raised when an account is not found."""

    def __init__(self, account_id: str, message: str | None = None) -> None:
        self.account_id = account_id
        default_message = f"Account {account_id} not found"
        super().__init__(message or default_message)


class TransactionNotFoundError(MyBudgetError):
    """Raised when a transaction is not found."""

    def __init__(self, transaction_id: str, message: str | None = None) -> None:
        self.transaction_id = transaction_id
        default_message = f"Transaction {transaction_id} not found"
        super().__init__(message or default_message)


class AuthenticationError(MyBudgetError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class AuthorizationError(MyBudgetError):
    """Raised when a user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized to perform this action") -> None:
        super().__init__(message)
