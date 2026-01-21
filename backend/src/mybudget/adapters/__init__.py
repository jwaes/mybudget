"""Bank provider adapters for external bank integrations."""
from mybudget.adapters.base import BankProviderAdapter
from mybudget.adapters.enablebanking_adapter import (
    EnableBankingAdapter,
    EnableBankingAPIError,
    EnableBankingAuthError,
    EnableBankingError,
    EnableBankingRateLimitError,
)
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
from mybudget.config import settings


def get_bank_adapter(provider: str | None = None) -> BankProviderAdapter:
    """Factory function to get the appropriate bank adapter.

    Args:
        provider: Provider name ('gocardless', 'enablebanking', 'mock').
                  If None, uses the BANK_PROVIDER setting.

    Returns:
        BankProviderAdapter instance.

    Raises:
        ValueError: If provider is not supported.
    """
    provider = provider or settings.BANK_PROVIDER

    if provider == "gocardless":
        return GoCardlessAdapter()
    elif provider == "enablebanking":
        return EnableBankingAdapter()
    elif provider == "mock":
        return MockBankAdapter()
    else:
        raise ValueError(f"Unsupported bank provider: {provider}")


__all__ = [
    # Base
    "BankProviderAdapter",
    # Factory
    "get_bank_adapter",
    # GoCardless
    "GoCardlessAdapter",
    "GoCardlessError",
    "GoCardlessAPIError",
    "GoCardlessAuthError",
    "GoCardlessRateLimitError",
    # EnableBanking
    "EnableBankingAdapter",
    "EnableBankingError",
    "EnableBankingAPIError",
    "EnableBankingAuthError",
    "EnableBankingRateLimitError",
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
