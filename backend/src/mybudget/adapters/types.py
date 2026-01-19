"""
Provider adapter types for bank feed integration.

These dataclasses represent normalized data from bank providers,
allowing different providers to be abstracted behind a common interface.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class ProviderAccountType(str, Enum):
    """Normalized account type from provider."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT = "CREDIT"
    LOAN = "LOAN"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"


class ProviderTransactionStatus(str, Enum):
    """Transaction status from provider."""

    PENDING = "PENDING"
    BOOKED = "BOOKED"


@dataclass(frozen=True)
class Institution:
    """Bank institution information from provider."""

    id: str
    name: str
    bic: str | None = None
    logo_url: str | None = None
    countries: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Convert countries list to tuple if needed."""
        if isinstance(self.countries, list):
            object.__setattr__(self, "countries", tuple(self.countries))


@dataclass(frozen=True)
class ProviderAccount:
    """Account information from provider."""

    id: str
    name: str | None = None
    iban: str | None = None
    account_number_masked: str | None = None
    account_type: ProviderAccountType = ProviderAccountType.OTHER
    currency: str = "EUR"
    balance: Decimal | None = None
    balance_date: datetime | None = None
    owner_name: str | None = None


@dataclass(frozen=True)
class ProviderTransaction:
    """Transaction from provider."""

    id: str
    date: date
    amount: Decimal
    currency: str
    description: str
    status: ProviderTransactionStatus = ProviderTransactionStatus.BOOKED
    creditor_name: str | None = None
    debtor_name: str | None = None
    reference: str | None = None
    internal_reference: str | None = None
    bank_transaction_code: str | None = None
    booking_date: date | None = None
    value_date: date | None = None

    @property
    def payee(self) -> str:
        """Get payee name (creditor for outgoing, debtor for incoming)."""
        if self.amount < 0:
            return self.creditor_name or self.description
        return self.debtor_name or self.description


@dataclass(frozen=True)
class RequisitionResponse:
    """Response from creating a bank connection requisition."""

    id: str
    link: str
    reference: str
    status: str


@dataclass(frozen=True)
class AccountAccessResponse:
    """Response containing account access details after OAuth completion."""

    requisition_id: str
    accounts: list[str]
    institution_id: str
    status: str
    access_valid_until: datetime | None = None


@dataclass
class ProviderError:
    """Error from provider API."""

    code: str
    message: str
    detail: str | None = None
    recoverable: bool = False
