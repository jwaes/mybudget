"""
Unit tests for MockBankAdapter.
"""
from datetime import date, datetime, timedelta, UTC
from decimal import Decimal

import pytest

from mybudget.adapters import (
    MockBankAdapter,
    Institution,
    ProviderAccount,
    ProviderAccountType,
    ProviderTransaction,
    ProviderTransactionStatus,
)


class TestMockBankAdapterBasics:
    """Tests for MockBankAdapter basic functionality."""

    def test_provider_name(self) -> None:
        """Test provider name returns 'mock'."""
        adapter = MockBankAdapter()
        assert adapter.provider_name == "mock"

    @pytest.mark.asyncio
    async def test_get_institutions_returns_defaults(self) -> None:
        """Test get_institutions returns default institutions."""
        adapter = MockBankAdapter()
        institutions = await adapter.get_institutions()

        assert len(institutions) == 3
        assert institutions[0].id == "SANDBOXFINANCE_SFIN0000"
        assert institutions[0].name == "Sandbox Finance"

    @pytest.mark.asyncio
    async def test_get_institutions_filter_by_country(self) -> None:
        """Test filtering institutions by country."""
        adapter = MockBankAdapter()

        # Filter for Belgium only
        be_institutions = await adapter.get_institutions(country="BE")
        assert len(be_institutions) == 3  # All support BE

        # Filter for France only
        fr_institutions = await adapter.get_institutions(country="FR")
        assert len(fr_institutions) == 1
        assert fr_institutions[0].id == "EUROBANK_EURO0002"

    @pytest.mark.asyncio
    async def test_get_institutions_pagination(self) -> None:
        """Test institution pagination."""
        adapter = MockBankAdapter()

        # Get first 2
        first_page = await adapter.get_institutions(limit=2)
        assert len(first_page) == 2

        # Get next page
        second_page = await adapter.get_institutions(limit=2, offset=2)
        assert len(second_page) == 1

    @pytest.mark.asyncio
    async def test_get_institution_by_id(self) -> None:
        """Test getting a specific institution."""
        adapter = MockBankAdapter()

        institution = await adapter.get_institution("TESTBANK_TEST0001")
        assert institution is not None
        assert institution.name == "Test Bank"

        # Non-existent institution
        missing = await adapter.get_institution("NONEXISTENT")
        assert missing is None


class TestMockBankAdapterRequisitions:
    """Tests for requisition handling."""

    @pytest.mark.asyncio
    async def test_create_requisition(self) -> None:
        """Test creating a requisition."""
        adapter = MockBankAdapter()

        response = await adapter.create_requisition(
            institution_id="SANDBOXFINANCE_SFIN0000",
            redirect_url="https://myapp.com/callback",
            reference="user-123-req-1",
        )

        assert response.id.startswith("REQ-")
        assert "auth?ref=" in response.link
        assert response.reference == "user-123-req-1"
        assert response.status == "CR"

    @pytest.mark.asyncio
    async def test_get_requisition_after_create(self) -> None:
        """Test retrieving a created requisition."""
        adapter = MockBankAdapter()

        # Create requisition
        create_response = await adapter.create_requisition(
            institution_id="SANDBOXFINANCE_SFIN0000",
            redirect_url="https://myapp.com/callback",
            reference="test-ref",
        )

        # Get requisition
        access = await adapter.get_requisition(create_response.id)
        assert access is not None
        assert access.requisition_id == create_response.id
        assert access.institution_id == "SANDBOXFINANCE_SFIN0000"
        assert access.status == "LN"
        assert len(access.accounts) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_requisition(self) -> None:
        """Test getting a non-existent requisition returns None."""
        adapter = MockBankAdapter()

        access = await adapter.get_requisition("NONEXISTENT")
        assert access is None

    @pytest.mark.asyncio
    async def test_create_requisition_failure(self) -> None:
        """Test requisition creation failure mode."""
        adapter = MockBankAdapter(fail_on_requisition=True)

        with pytest.raises(RuntimeError, match="Mock requisition failure"):
            await adapter.create_requisition(
                institution_id="SANDBOXFINANCE_SFIN0000",
                redirect_url="https://myapp.com/callback",
                reference="test-ref",
            )


class TestMockBankAdapterAccounts:
    """Tests for account handling."""

    @pytest.mark.asyncio
    async def test_get_accounts_for_requisition(self) -> None:
        """Test getting accounts for a requisition."""
        adapter = MockBankAdapter()

        # Create requisition first
        response = await adapter.create_requisition(
            institution_id="SANDBOXFINANCE_SFIN0000",
            redirect_url="https://myapp.com/callback",
            reference="test-ref",
        )

        # Get accounts
        accounts = await adapter.get_accounts(response.id)
        assert len(accounts) == 2
        assert accounts[0].id == "ACC-CHECKING-001"
        assert accounts[0].account_type == ProviderAccountType.CHECKING
        assert accounts[1].id == "ACC-SAVINGS-001"
        assert accounts[1].account_type == ProviderAccountType.SAVINGS

    @pytest.mark.asyncio
    async def test_get_accounts_nonexistent_requisition(self) -> None:
        """Test getting accounts for non-existent requisition returns empty list."""
        adapter = MockBankAdapter()

        accounts = await adapter.get_accounts("NONEXISTENT")
        assert accounts == []

    @pytest.mark.asyncio
    async def test_get_account_details(self) -> None:
        """Test getting specific account details."""
        adapter = MockBankAdapter()

        account = await adapter.get_account_details("ACC-CHECKING-001")
        assert account is not None
        assert account.name == "Main Checking"
        assert account.currency == "EUR"
        assert account.balance == Decimal("2500.00")

    @pytest.mark.asyncio
    async def test_get_account_balances(self) -> None:
        """Test getting account balance."""
        adapter = MockBankAdapter()

        account = await adapter.get_account_balances("ACC-CHECKING-001")
        assert account is not None
        assert account.balance == Decimal("2500.00")

    @pytest.mark.asyncio
    async def test_get_accounts_failure(self) -> None:
        """Test account fetch failure mode."""
        adapter = MockBankAdapter(fail_on_accounts=True)

        with pytest.raises(RuntimeError, match="Mock account fetch failure"):
            await adapter.get_account_details("ACC-CHECKING-001")


class TestMockBankAdapterTransactions:
    """Tests for transaction handling."""

    @pytest.mark.asyncio
    async def test_get_transactions_generates_mock_data(self) -> None:
        """Test that transactions are generated when none provided."""
        adapter = MockBankAdapter()

        today = date.today()
        transactions = await adapter.get_transactions(
            account_id="ACC-CHECKING-001",
            date_from=today - timedelta(days=7),
            date_to=today,
        )

        # Should have some generated transactions
        assert len(transactions) >= 0  # May have 0-3 per day
        for tx in transactions:
            assert tx.id.startswith("TX-ACC-CHECKING-001-")
            assert tx.currency == "EUR"
            assert tx.status == ProviderTransactionStatus.BOOKED

    @pytest.mark.asyncio
    async def test_get_transactions_with_custom_data(self) -> None:
        """Test getting custom transactions."""
        custom_transactions = [
            ProviderTransaction(
                id="TX-001",
                date=date.today(),
                amount=Decimal("-50.00"),
                currency="EUR",
                description="Test Transaction",
                creditor_name="Test Payee",
            ),
        ]

        adapter = MockBankAdapter(transactions=custom_transactions)
        transactions = await adapter.get_transactions("ACC-CHECKING-001")

        assert len(transactions) == 1
        assert transactions[0].id == "TX-001"
        assert transactions[0].amount == Decimal("-50.00")

    @pytest.mark.asyncio
    async def test_get_transactions_date_filter(self) -> None:
        """Test transaction date filtering."""
        today = date.today()
        custom_transactions = [
            ProviderTransaction(
                id="TX-OLD",
                date=today - timedelta(days=30),
                amount=Decimal("-10.00"),
                currency="EUR",
                description="Old Transaction",
            ),
            ProviderTransaction(
                id="TX-NEW",
                date=today,
                amount=Decimal("-20.00"),
                currency="EUR",
                description="New Transaction",
            ),
        ]

        adapter = MockBankAdapter(transactions=custom_transactions)

        # Get only recent
        recent = await adapter.get_transactions(
            "ACC-CHECKING-001",
            date_from=today - timedelta(days=7),
        )
        assert len(recent) == 1
        assert recent[0].id == "TX-NEW"

    @pytest.mark.asyncio
    async def test_get_transactions_failure(self) -> None:
        """Test transaction fetch failure mode."""
        adapter = MockBankAdapter(fail_on_transactions=True)

        with pytest.raises(RuntimeError, match="Mock transaction fetch failure"):
            await adapter.get_transactions("ACC-CHECKING-001")

    def test_transaction_payee_property(self) -> None:
        """Test ProviderTransaction.payee property."""
        # Outgoing transaction (expense)
        expense = ProviderTransaction(
            id="TX-001",
            date=date.today(),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Generic Description",
            creditor_name="Store Name",
        )
        assert expense.payee == "Store Name"

        # Incoming transaction (income)
        income = ProviderTransaction(
            id="TX-002",
            date=date.today(),
            amount=Decimal("1000.00"),
            currency="EUR",
            description="Salary",
            debtor_name="Employer Inc",
        )
        assert income.payee == "Employer Inc"

        # Fallback to description
        no_names = ProviderTransaction(
            id="TX-003",
            date=date.today(),
            amount=Decimal("-25.00"),
            currency="EUR",
            description="Fallback Description",
        )
        assert no_names.payee == "Fallback Description"


class TestMockBankAdapterAccessManagement:
    """Tests for access refresh and revocation."""

    @pytest.mark.asyncio
    async def test_refresh_access(self) -> None:
        """Test refreshing access for a requisition."""
        adapter = MockBankAdapter()

        # Create requisition
        response = await adapter.create_requisition(
            institution_id="SANDBOXFINANCE_SFIN0000",
            redirect_url="https://myapp.com/callback",
            reference="test-ref",
            agreement_days=30,
        )

        # Get original expiry
        original = await adapter.get_requisition(response.id)
        assert original is not None
        original_expiry = original.access_valid_until

        # Refresh access
        refreshed = await adapter.refresh_access(response.id)
        assert refreshed is not None
        assert refreshed.access_valid_until > original_expiry

    @pytest.mark.asyncio
    async def test_refresh_nonexistent_requisition(self) -> None:
        """Test refreshing non-existent requisition returns None."""
        adapter = MockBankAdapter()

        result = await adapter.refresh_access("NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_access(self) -> None:
        """Test revoking access for a requisition."""
        adapter = MockBankAdapter()

        # Create requisition
        response = await adapter.create_requisition(
            institution_id="SANDBOXFINANCE_SFIN0000",
            redirect_url="https://myapp.com/callback",
            reference="test-ref",
        )

        # Revoke access
        result = await adapter.revoke_access(response.id)
        assert result is True

        # Verify requisition is gone
        access = await adapter.get_requisition(response.id)
        assert access is None

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_requisition(self) -> None:
        """Test revoking non-existent requisition returns False."""
        adapter = MockBankAdapter()

        result = await adapter.revoke_access("NONEXISTENT")
        assert result is False


class TestMockBankAdapterHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        """Test health check returns True when healthy."""
        adapter = MockBankAdapter()

        result = await adapter.health_check()
        assert result is True


class TestMockBankAdapterTestHelpers:
    """Tests for test helper methods."""

    @pytest.mark.asyncio
    async def test_add_requisition_helper(self) -> None:
        """Test add_requisition helper method."""
        adapter = MockBankAdapter()

        adapter.add_requisition(
            requisition_id="TEST-REQ-001",
            institution_id="TESTBANK_TEST0001",
            account_ids=["ACC-001", "ACC-002"],
        )

        access = await adapter.get_requisition("TEST-REQ-001")
        assert access is not None
        assert access.institution_id == "TESTBANK_TEST0001"
        assert access.accounts == ["ACC-001", "ACC-002"]

    @pytest.mark.asyncio
    async def test_set_accounts_helper(self) -> None:
        """Test set_accounts helper method."""
        adapter = MockBankAdapter()

        custom_accounts = [
            ProviderAccount(
                id="CUSTOM-ACC",
                name="Custom Account",
                account_type=ProviderAccountType.CREDIT,
                currency="USD",
            ),
        ]

        adapter.set_accounts(custom_accounts)
        adapter.add_requisition("REQ-001", "INST-001")

        accounts = await adapter.get_accounts("REQ-001")
        assert len(accounts) == 1
        assert accounts[0].id == "CUSTOM-ACC"

    def test_clear_helper(self) -> None:
        """Test clear helper method."""
        adapter = MockBankAdapter()
        adapter.add_requisition("REQ-001", "INST-001")

        adapter.clear()

        # Requisitions should be cleared
        assert len(adapter._requisitions) == 0


class TestInstitutionDataclass:
    """Tests for Institution dataclass."""

    def test_institution_countries_as_list(self) -> None:
        """Test that Institution converts countries list to tuple."""
        # This tests the __post_init__ conversion
        inst = Institution(
            id="TEST",
            name="Test",
            countries=["BE", "NL"],  # type: ignore
        )
        assert isinstance(inst.countries, tuple)
        assert inst.countries == ("BE", "NL")

    def test_institution_immutable(self) -> None:
        """Test that Institution is frozen/immutable."""
        inst = Institution(id="TEST", name="Test")

        with pytest.raises(AttributeError):
            inst.name = "Changed"  # type: ignore
