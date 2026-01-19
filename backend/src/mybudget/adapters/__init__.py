"""Bank provider adapters for external bank integrations."""
from mybudget.adapters.base import BankProviderAdapter
from mybudget.adapters.gocardless_adapter import (
    GoCardlessAdapter,
    GoCardlessAPIError,
    GoCardlessAuthError,
    GoCardlessError,
    GoCardlessRateLimitError,
)
from mybudget.adapters.mock_adapter import MockBankAdapter
from mybudget.adapters.types import (
    AccountAccessResponse,
    Institution,
    ProviderAccount,
    ProviderAccountType,
    ProviderError,
    ProviderTransaction,
    ProviderTransactionStatus,
    RequisitionResponse,
)

__all__ = [
    # Base
    "BankProviderAdapter",
    # GoCardless
    "GoCardlessAdapter",
    "GoCardlessError",
    "GoCardlessAPIError",
    "GoCardlessAuthError",
    "GoCardlessRateLimitError",
    # Mock
    "MockBankAdapter",
    # Types
    "Institution",
    "ProviderAccount",
    "ProviderAccountType",
    "ProviderTransaction",
    "ProviderTransactionStatus",
    "RequisitionResponse",
    "AccountAccessResponse",
    "ProviderError",
]
