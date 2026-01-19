"""
Mock bank provider adapter for testing.

This adapter provides predictable, configurable responses for testing
the bank feed integration without connecting to real bank APIs.
"""
from datetime import date, datetime, timedelta, UTC
from decimal import Decimal
from uuid import uuid4

from mybudget.adapters.base import BankProviderAdapter
from mybudget.adapters.types import (
    AccountAccessResponse,
    Institution,
    ProviderAccount,
    ProviderAccountType,
    ProviderTransaction,
    ProviderTransactionStatus,
    RequisitionResponse,
)


class MockBankAdapter(BankProviderAdapter):
    """Mock bank provider adapter for testing."""

    # Default mock data
    DEFAULT_INSTITUTIONS: list[Institution] = [
        Institution(
            id="SANDBOXFINANCE_SFIN0000",
            name="Sandbox Finance",
            bic="SFINBEXX",
            logo_url="https://example.com/sandbox-logo.png",
            countries=("BE", "NL", "DE"),
        ),
        Institution(
            id="TESTBANK_TEST0001",
            name="Test Bank",
            bic="TESTBEXX",
            logo_url="https://example.com/test-logo.png",
            countries=("BE",),
        ),
        Institution(
            id="EUROBANK_EURO0002",
            name="Euro Bank",
            bic="EUROBEXX",
            logo_url="https://example.com/euro-logo.png",
            countries=("BE", "NL", "FR", "DE"),
        ),
    ]

    DEFAULT_ACCOUNTS: list[ProviderAccount] = [
        ProviderAccount(
            id="ACC-CHECKING-001",
            name="Main Checking",
            iban="BE68539007547034",
            account_number_masked="****7034",
            account_type=ProviderAccountType.CHECKING,
            currency="EUR",
            balance=Decimal("2500.00"),
            balance_date=datetime.now(UTC),
        ),
        ProviderAccount(
            id="ACC-SAVINGS-001",
            name="Savings Account",
            iban="BE71096123456789",
            account_number_masked="****6789",
            account_type=ProviderAccountType.SAVINGS,
            currency="EUR",
            balance=Decimal("15000.00"),
            balance_date=datetime.now(UTC),
        ),
    ]

    def __init__(
        self,
        *,
        institutions: list[Institution] | None = None,
        accounts: list[ProviderAccount] | None = None,
        transactions: list[ProviderTransaction] | None = None,
        fail_on_requisition: bool = False,
        fail_on_accounts: bool = False,
        fail_on_transactions: bool = False,
    ) -> None:
        """
        Initialize mock adapter with optional custom data.

        Args:
            institutions: Custom institutions to return
            accounts: Custom accounts to return
            transactions: Custom transactions to return
            fail_on_requisition: Simulate requisition creation failure
            fail_on_accounts: Simulate account fetch failure
            fail_on_transactions: Simulate transaction fetch failure
        """
        self._institutions = institutions or self.DEFAULT_INSTITUTIONS
        self._accounts = accounts or self.DEFAULT_ACCOUNTS
        self._transactions = transactions or []
        self._fail_on_requisition = fail_on_requisition
        self._fail_on_accounts = fail_on_accounts
        self._fail_on_transactions = fail_on_transactions

        # Track created requisitions
        self._requisitions: dict[str, AccountAccessResponse] = {}

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return "mock"

    async def get_institutions(
        self,
        country: str | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Institution]:
        """Get list of available banking institutions."""
        institutions = self._institutions
        if country:
            institutions = [
                inst for inst in institutions if country in inst.countries
            ]
        return institutions[offset : offset + limit]

    async def get_institution(self, institution_id: str) -> Institution | None:
        """Get details for a specific institution."""
        for inst in self._institutions:
            if inst.id == institution_id:
                return inst
        return None

    async def create_requisition(
        self,
        institution_id: str,
        redirect_url: str,
        reference: str,
        *,
        user_language: str = "EN",
        agreement_days: int = 90,
        max_historical_days: int = 90,
    ) -> RequisitionResponse:
        """Create a requisition for bank access."""
        if self._fail_on_requisition:
            raise RuntimeError("Mock requisition failure")

        requisition_id = f"REQ-{uuid4().hex[:8].upper()}"
        link = f"https://mock-bank.example.com/auth?ref={requisition_id}"

        # Store requisition for later retrieval
        self._requisitions[requisition_id] = AccountAccessResponse(
            requisition_id=requisition_id,
            accounts=[acc.id for acc in self._accounts],
            institution_id=institution_id,
            status="LN",  # Linked status
            access_valid_until=datetime.now(UTC) + timedelta(days=agreement_days),
        )

        return RequisitionResponse(
            id=requisition_id,
            link=link,
            reference=reference,
            status="CR",  # Created status
        )

    async def get_requisition(self, requisition_id: str) -> AccountAccessResponse | None:
        """Get the status and details of a requisition."""
        return self._requisitions.get(requisition_id)

    async def get_accounts(
        self,
        requisition_id: str,
    ) -> list[ProviderAccount]:
        """Get accounts linked to a requisition."""
        if self._fail_on_accounts:
            raise RuntimeError("Mock account fetch failure")

        if requisition_id not in self._requisitions:
            return []
        return self._accounts

    async def get_account_details(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """Get details for a specific account."""
        if self._fail_on_accounts:
            raise RuntimeError("Mock account fetch failure")

        for acc in self._accounts:
            if acc.id == account_id:
                return acc
        return None

    async def get_account_balances(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """Get current balance for an account."""
        return await self.get_account_details(account_id)

    async def get_transactions(
        self,
        account_id: str,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ProviderTransaction]:
        """Get transactions for an account."""
        if self._fail_on_transactions:
            raise RuntimeError("Mock transaction fetch failure")

        # If no custom transactions provided, generate some mock ones
        if not self._transactions:
            return self._generate_mock_transactions(account_id, date_from, date_to)

        # Filter by date if provided
        transactions = self._transactions
        if date_from:
            transactions = [t for t in transactions if t.date >= date_from]
        if date_to:
            transactions = [t for t in transactions if t.date <= date_to]
        return transactions

    def _generate_mock_transactions(
        self,
        account_id: str,
        date_from: date | None,
        date_to: date | None,
    ) -> list[ProviderTransaction]:
        """Generate mock transactions for testing."""
        today = date.today()
        start_date = date_from or (today - timedelta(days=30))
        end_date = date_to or today

        mock_payees = [
            ("Grocery Store", Decimal("-85.50")),
            ("Electric Company", Decimal("-120.00")),
            ("Employer Inc", Decimal("3500.00")),
            ("Coffee Shop", Decimal("-4.50")),
            ("Online Store", Decimal("-59.99")),
            ("Gas Station", Decimal("-65.00")),
            ("Restaurant", Decimal("-42.00")),
            ("Pharmacy", Decimal("-23.50")),
        ]

        transactions = []
        current_date = start_date
        tx_counter = 0

        while current_date <= end_date:
            # Generate 0-3 transactions per day
            num_transactions = hash(str(current_date) + account_id) % 4
            for _ in range(num_transactions):
                payee, amount = mock_payees[tx_counter % len(mock_payees)]
                transactions.append(
                    ProviderTransaction(
                        id=f"TX-{account_id}-{current_date.isoformat()}-{tx_counter}",
                        date=current_date,
                        amount=amount,
                        currency="EUR",
                        description=payee,
                        status=ProviderTransactionStatus.BOOKED,
                        creditor_name=payee if amount < 0 else None,
                        debtor_name=payee if amount > 0 else None,
                        reference=f"REF{tx_counter:06d}",
                        booking_date=current_date,
                        value_date=current_date,
                    )
                )
                tx_counter += 1
            current_date += timedelta(days=1)

        return transactions

    async def refresh_access(
        self,
        requisition_id: str,
    ) -> AccountAccessResponse | None:
        """Refresh access token for a requisition."""
        if requisition_id not in self._requisitions:
            return None

        # Update access expiry
        current = self._requisitions[requisition_id]
        self._requisitions[requisition_id] = AccountAccessResponse(
            requisition_id=current.requisition_id,
            accounts=current.accounts,
            institution_id=current.institution_id,
            status=current.status,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
        )
        return self._requisitions[requisition_id]

    async def revoke_access(
        self,
        requisition_id: str,
    ) -> bool:
        """Revoke access and delete requisition."""
        if requisition_id in self._requisitions:
            del self._requisitions[requisition_id]
            return True
        return False

    # Test helper methods
    def add_requisition(
        self,
        requisition_id: str,
        institution_id: str,
        account_ids: list[str] | None = None,
        status: str = "LN",
    ) -> None:
        """Add a requisition for testing."""
        self._requisitions[requisition_id] = AccountAccessResponse(
            requisition_id=requisition_id,
            accounts=account_ids or [acc.id for acc in self._accounts],
            institution_id=institution_id,
            status=status,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
        )

    def set_accounts(self, accounts: list[ProviderAccount]) -> None:
        """Set custom accounts for testing."""
        self._accounts = accounts

    def set_transactions(self, transactions: list[ProviderTransaction]) -> None:
        """Set custom transactions for testing."""
        self._transactions = transactions

    def clear(self) -> None:
        """Clear all stored data."""
        self._requisitions.clear()
        self._accounts = self.DEFAULT_ACCOUNTS
        self._transactions = []
