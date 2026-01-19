"""
Unit tests for GoCardless Bank Account Data adapter.

Uses mocked HTTP responses to test the adapter without hitting the real API.
"""
from datetime import date, datetime, timedelta, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mybudget.adapters.gocardless_adapter import (
    GoCardlessAdapter,
    GoCardlessAPIError,
    GoCardlessAuthError,
    GoCardlessRateLimitError,
)
from mybudget.adapters.types import (
    ProviderAccountType,
    ProviderTransactionStatus,
)


# Sample API responses based on GoCardless Bank Account Data API documentation
SAMPLE_TOKEN_RESPONSE = {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access_expires": 86400,
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_expires": 2592000,
}

SAMPLE_INSTITUTIONS_RESPONSE = [
    {
        "id": "SANDBOXFINANCE_SFIN0000",
        "name": "Sandbox Finance",
        "bic": "SFINBEXX",
        "logo": "https://cdn.nordigen.com/ais/SANDBOXFINANCE_SFIN0000.png",
        "countries": ["BE", "NL", "DE"],
        "transaction_total_days": "90",
    },
    {
        "id": "ING_INGBNL2A",
        "name": "ING",
        "bic": "INGBNL2A",
        "logo": "https://cdn.nordigen.com/ais/ING_INGBNL2A.png",
        "countries": ["NL"],
        "transaction_total_days": "540",
    },
]

SAMPLE_REQUISITION_RESPONSE = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created": "2024-01-15T10:30:00.000000Z",
    "redirect": "https://myapp.com/callback",
    "status": "CR",
    "institution_id": "SANDBOXFINANCE_SFIN0000",
    "agreement": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
    "reference": "user-123-req-1",
    "accounts": [],
    "link": "https://ob.gocardless.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/SANDBOXFINANCE_SFIN0000",
}

SAMPLE_REQUISITION_LINKED_RESPONSE = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created": "2024-01-15T10:30:00.000000Z",
    "redirect": "https://myapp.com/callback",
    "status": "LN",
    "institution_id": "SANDBOXFINANCE_SFIN0000",
    "agreement": "3fa85f64-5717-4562-b3fc-2c963f66afa7",
    "reference": "user-123-req-1",
    "accounts": [
        "a1b2c3d4-5678-90ab-cdef-1234567890ab",
        "b2c3d4e5-6789-01bc-defg-2345678901bc",
    ],
    "link": "https://ob.gocardless.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/SANDBOXFINANCE_SFIN0000",
}

SAMPLE_ACCOUNT_DETAILS_RESPONSE = {
    "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "created": "2024-01-15T10:35:00.000000Z",
    "last_accessed": "2024-01-15T10:40:00.000000Z",
    "iban": "BE68539007547034",
    "institution_id": "SANDBOXFINANCE_SFIN0000",
    "status": "READY",
    "owner_name": "John Doe",
}

SAMPLE_ACCOUNT_METADATA_RESPONSE = {
    "account": {
        "resourceId": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
        "iban": "BE68539007547034",
        "currency": "EUR",
        "ownerName": "John Doe",
        "name": "Current Account",
        "product": "Current Account",
        "cashAccountType": "CACC",
    }
}

SAMPLE_BALANCES_RESPONSE = {
    "balances": [
        {
            "balanceAmount": {"amount": "2500.00", "currency": "EUR"},
            "balanceType": "interimAvailable",
            "referenceDate": "2024-01-15",
        },
        {
            "balanceAmount": {"amount": "2600.00", "currency": "EUR"},
            "balanceType": "closingBooked",
            "referenceDate": "2024-01-14",
        },
    ]
}

SAMPLE_TRANSACTIONS_RESPONSE = {
    "transactions": {
        "booked": [
            {
                "transactionId": "2024011500001234",
                "bookingDate": "2024-01-15",
                "valueDate": "2024-01-15",
                "transactionAmount": {"amount": "-50.00", "currency": "EUR"},
                "creditorName": "Grocery Store",
                "remittanceInformationUnstructured": "Purchase at Grocery Store",
                "internalTransactionId": "abcd1234",
            },
            {
                "transactionId": "2024011400001235",
                "bookingDate": "2024-01-14",
                "valueDate": "2024-01-14",
                "transactionAmount": {"amount": "3500.00", "currency": "EUR"},
                "debtorName": "Employer Inc",
                "remittanceInformationUnstructured": "Salary January 2024",
                "internalTransactionId": "efgh5678",
            },
        ],
        "pending": [
            {
                "transactionId": "2024011600001236",
                "valueDate": "2024-01-16",
                "transactionAmount": {"amount": "-25.00", "currency": "EUR"},
                "creditorName": "Coffee Shop",
                "remittanceInformationUnstructured": "Coffee purchase",
            },
        ],
    }
}


@pytest.fixture
def mock_settings():
    """Mock settings for GoCardless configuration."""
    with patch("mybudget.adapters.gocardless_adapter.settings") as mock:
        mock.GOCARDLESS_SECRET_ID = "test-secret-id"
        mock.GOCARDLESS_SECRET_KEY = "test-secret-key"
        mock.GOCARDLESS_BASE_URL = "https://bankaccountdata.gocardless.com/api/v2"
        yield mock


@pytest.fixture
def adapter(mock_settings):
    """Create GoCardless adapter instance."""
    return GoCardlessAdapter()


class TestGoCardlessAdapterBasics:
    """Tests for GoCardlessAdapter basic functionality."""

    def test_provider_name(self, adapter) -> None:
        """Test provider name returns 'gocardless'."""
        assert adapter.provider_name == "gocardless"

    def test_adapter_requires_credentials(self) -> None:
        """Test adapter raises error without credentials."""
        with patch("mybudget.adapters.gocardless_adapter.settings") as mock:
            mock.GOCARDLESS_SECRET_ID = None
            mock.GOCARDLESS_SECRET_KEY = None
            mock.GOCARDLESS_BASE_URL = "https://bankaccountdata.gocardless.com/api/v2"

            with pytest.raises(GoCardlessAuthError, match="credentials"):
                GoCardlessAdapter()


class TestGoCardlessAdapterInstitutions:
    """Tests for institution-related methods."""

    @pytest.mark.asyncio
    async def test_get_institutions(self, adapter) -> None:
        """Test getting list of institutions."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_INSTITUTIONS_RESPONSE

            institutions = await adapter.get_institutions()

            assert len(institutions) == 2
            assert institutions[0].id == "SANDBOXFINANCE_SFIN0000"
            assert institutions[0].name == "Sandbox Finance"
            assert institutions[0].bic == "SFINBEXX"
            assert "BE" in institutions[0].countries
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_institutions_by_country(self, adapter) -> None:
        """Test filtering institutions by country."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [SAMPLE_INSTITUTIONS_RESPONSE[1]]  # ING only

            institutions = await adapter.get_institutions(country="NL")

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["params"]["country"] == "NL"

    @pytest.mark.asyncio
    async def test_get_institution_by_id(self, adapter) -> None:
        """Test getting a specific institution."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_INSTITUTIONS_RESPONSE[0]

            institution = await adapter.get_institution("SANDBOXFINANCE_SFIN0000")

            assert institution is not None
            assert institution.id == "SANDBOXFINANCE_SFIN0000"
            assert institution.name == "Sandbox Finance"

    @pytest.mark.asyncio
    async def test_get_institution_not_found(self, adapter) -> None:
        """Test getting non-existent institution returns None."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GoCardlessAPIError("Not found", status_code=404)

            institution = await adapter.get_institution("NONEXISTENT")

            assert institution is None


class TestGoCardlessAdapterRequisitions:
    """Tests for requisition handling."""

    @pytest.mark.asyncio
    async def test_create_requisition(self, adapter) -> None:
        """Test creating a requisition."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            # First call creates agreement, second creates requisition
            mock_request.side_effect = [
                {"id": "3fa85f64-5717-4562-b3fc-2c963f66afa7"},  # Agreement
                SAMPLE_REQUISITION_RESPONSE,  # Requisition
            ]

            response = await adapter.create_requisition(
                institution_id="SANDBOXFINANCE_SFIN0000",
                redirect_url="https://myapp.com/callback",
                reference="user-123-req-1",
            )

            assert response.id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            assert "ob.gocardless.com" in response.link
            assert response.reference == "user-123-req-1"
            assert response.status == "CR"

    @pytest.mark.asyncio
    async def test_create_requisition_with_options(self, adapter) -> None:
        """Test creating a requisition with custom options."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                {"id": "agreement-id"},
                SAMPLE_REQUISITION_RESPONSE,
            ]

            await adapter.create_requisition(
                institution_id="SANDBOXFINANCE_SFIN0000",
                redirect_url="https://myapp.com/callback",
                reference="test-ref",
                user_language="NL",
                agreement_days=180,
                max_historical_days=365,
            )

            # Check agreement creation call
            agreement_call = mock_request.call_args_list[0]
            assert agreement_call[1]["json"]["access_valid_for_days"] == 180
            assert agreement_call[1]["json"]["max_historical_days"] == 365

    @pytest.mark.asyncio
    async def test_get_requisition(self, adapter) -> None:
        """Test getting a requisition's status."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_REQUISITION_LINKED_RESPONSE

            access = await adapter.get_requisition("3fa85f64-5717-4562-b3fc-2c963f66afa6")

            assert access is not None
            assert access.requisition_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            assert access.institution_id == "SANDBOXFINANCE_SFIN0000"
            assert access.status == "LN"
            assert len(access.accounts) == 2

    @pytest.mark.asyncio
    async def test_get_requisition_not_found(self, adapter) -> None:
        """Test getting non-existent requisition returns None."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GoCardlessAPIError("Not found", status_code=404)

            access = await adapter.get_requisition("nonexistent")

            assert access is None


class TestGoCardlessAdapterAccounts:
    """Tests for account-related methods."""

    @pytest.mark.asyncio
    async def test_get_accounts(self, adapter) -> None:
        """Test getting accounts for a requisition."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            # First call gets requisition, subsequent calls get account details
            mock_request.side_effect = [
                SAMPLE_REQUISITION_LINKED_RESPONSE,  # Requisition
                SAMPLE_ACCOUNT_DETAILS_RESPONSE,  # Account 1 basic
                SAMPLE_ACCOUNT_METADATA_RESPONSE,  # Account 1 metadata
                {  # Account 2 basic
                    "id": "b2c3d4e5-6789-01bc-defg-2345678901bc",
                    "iban": "BE71096123456789",
                    "institution_id": "SANDBOXFINANCE_SFIN0000",
                    "status": "READY",
                },
                {  # Account 2 metadata
                    "account": {
                        "iban": "BE71096123456789",
                        "currency": "EUR",
                        "name": "Savings Account",
                        "cashAccountType": "SVGS",
                    }
                },
            ]

            accounts = await adapter.get_accounts("3fa85f64-5717-4562-b3fc-2c963f66afa6")

            assert len(accounts) == 2
            assert accounts[0].id == "a1b2c3d4-5678-90ab-cdef-1234567890ab"
            assert accounts[0].iban == "BE68539007547034"
            assert accounts[0].name == "Current Account"

    @pytest.mark.asyncio
    async def test_get_account_details(self, adapter) -> None:
        """Test getting specific account details."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                SAMPLE_ACCOUNT_DETAILS_RESPONSE,
                SAMPLE_ACCOUNT_METADATA_RESPONSE,
            ]

            account = await adapter.get_account_details("a1b2c3d4-5678-90ab-cdef-1234567890ab")

            assert account is not None
            assert account.id == "a1b2c3d4-5678-90ab-cdef-1234567890ab"
            assert account.iban == "BE68539007547034"
            assert account.currency == "EUR"
            assert account.owner_name == "John Doe"
            assert account.account_type == ProviderAccountType.CHECKING

    @pytest.mark.asyncio
    async def test_get_account_balances(self, adapter) -> None:
        """Test getting account balances."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                SAMPLE_ACCOUNT_DETAILS_RESPONSE,
                SAMPLE_ACCOUNT_METADATA_RESPONSE,
                SAMPLE_BALANCES_RESPONSE,
            ]

            account = await adapter.get_account_balances("a1b2c3d4-5678-90ab-cdef-1234567890ab")

            assert account is not None
            assert account.balance == Decimal("2500.00")
            assert account.currency == "EUR"

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, adapter) -> None:
        """Test getting non-existent account returns None."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GoCardlessAPIError("Not found", status_code=404)

            account = await adapter.get_account_details("nonexistent")

            assert account is None


class TestGoCardlessAdapterTransactions:
    """Tests for transaction-related methods."""

    @pytest.mark.asyncio
    async def test_get_transactions(self, adapter) -> None:
        """Test getting transactions for an account."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_TRANSACTIONS_RESPONSE

            transactions = await adapter.get_transactions(
                account_id="a1b2c3d4-5678-90ab-cdef-1234567890ab"
            )

            # Should include both booked and pending
            assert len(transactions) == 3

            # Check booked transaction (expense)
            expense = next(t for t in transactions if t.amount < 0 and t.status == ProviderTransactionStatus.BOOKED)
            assert expense.amount == Decimal("-50.00")
            assert expense.creditor_name == "Grocery Store"

            # Check booked transaction (income)
            income = next(t for t in transactions if t.amount > 0)
            assert income.amount == Decimal("3500.00")
            assert income.debtor_name == "Employer Inc"

            # Check pending transaction
            pending = next(t for t in transactions if t.status == ProviderTransactionStatus.PENDING)
            assert pending.amount == Decimal("-25.00")

    @pytest.mark.asyncio
    async def test_get_transactions_with_date_filter(self, adapter) -> None:
        """Test getting transactions with date filter."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_TRANSACTIONS_RESPONSE

            await adapter.get_transactions(
                account_id="a1b2c3d4-5678-90ab-cdef-1234567890ab",
                date_from=date(2024, 1, 1),
                date_to=date(2024, 1, 31),
            )

            call_args = mock_request.call_args
            assert call_args[1]["params"]["date_from"] == "2024-01-01"
            assert call_args[1]["params"]["date_to"] == "2024-01-31"


class TestGoCardlessAdapterAccessManagement:
    """Tests for access refresh and revocation."""

    @pytest.mark.asyncio
    async def test_refresh_access(self, adapter) -> None:
        """Test refreshing access doesn't require API call for GoCardless."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_REQUISITION_LINKED_RESPONSE

            result = await adapter.refresh_access("3fa85f64-5717-4562-b3fc-2c963f66afa6")

            # GoCardless doesn't require token refresh, just returns current status
            assert result is not None
            assert result.requisition_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    @pytest.mark.asyncio
    async def test_revoke_access(self, adapter) -> None:
        """Test revoking access deletes the requisition."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await adapter.revoke_access("3fa85f64-5717-4562-b3fc-2c963f66afa6")

            assert result is True
            mock_request.assert_called_once()
            # Check that DELETE method was used (first positional argument)
            assert mock_request.call_args[0][0] == "DELETE"

    @pytest.mark.asyncio
    async def test_revoke_access_not_found(self, adapter) -> None:
        """Test revoking non-existent requisition returns False."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GoCardlessAPIError("Not found", status_code=404)

            result = await adapter.revoke_access("nonexistent")

            assert result is False


class TestGoCardlessAdapterErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, adapter) -> None:
        """Test rate limit error is properly raised."""
        # First mock getting the access token
        with patch.object(adapter, "_get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "test-token"

            # Then mock the client to return a rate limit error
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.json.return_value = {"detail": "Rate limit exceeded"}
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate limited", request=MagicMock(), response=mock_response
            )

            with patch.object(adapter._client, "request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(GoCardlessRateLimitError):
                    await adapter.get_institutions()

    @pytest.mark.asyncio
    async def test_auth_error(self, adapter) -> None:
        """Test authentication error is properly raised."""
        # First mock getting the access token
        with patch.object(adapter, "_get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "test-token"

            # Then mock the client to return an auth error
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"detail": "Invalid credentials"}
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response
            )

            with patch.object(adapter._client, "request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(GoCardlessAuthError):
                    await adapter.get_institutions()

    @pytest.mark.asyncio
    async def test_api_error_with_details(self, adapter) -> None:
        """Test API error includes response details."""
        # First mock getting the access token
        with patch.object(adapter, "_get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "test-token"

            # Then mock the client to return an API error
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "type": "validation_error",
                "detail": "Invalid institution_id",
            }
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Bad request", request=MagicMock(), response=mock_response
            )

            with patch.object(adapter._client, "request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                with pytest.raises(GoCardlessAPIError) as exc_info:
                    await adapter.get_institutions()

                assert exc_info.value.status_code == 400
                assert "Invalid institution_id" in str(exc_info.value)


class TestGoCardlessAdapterHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter) -> None:
        """Test health check returns True when API is accessible."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_INSTITUTIONS_RESPONSE[:1]

            result = await adapter.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, adapter) -> None:
        """Test health check returns False when API is not accessible."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = GoCardlessAPIError("Service unavailable", status_code=503)

            result = await adapter.health_check()

            assert result is False


class TestGoCardlessAdapterAccountTypeMapping:
    """Tests for account type mapping."""

    @pytest.mark.asyncio
    async def test_map_account_type_checking(self, adapter) -> None:
        """Test CACC maps to CHECKING."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                {"id": "acc1", "iban": "BE123", "status": "READY"},
                {"account": {"iban": "BE123", "cashAccountType": "CACC", "currency": "EUR"}},
            ]

            account = await adapter.get_account_details("acc1")
            assert account.account_type == ProviderAccountType.CHECKING

    @pytest.mark.asyncio
    async def test_map_account_type_savings(self, adapter) -> None:
        """Test SVGS maps to SAVINGS."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                {"id": "acc1", "iban": "BE123", "status": "READY"},
                {"account": {"iban": "BE123", "cashAccountType": "SVGS", "currency": "EUR"}},
            ]

            account = await adapter.get_account_details("acc1")
            assert account.account_type == ProviderAccountType.SAVINGS

    @pytest.mark.asyncio
    async def test_map_account_type_credit(self, adapter) -> None:
        """Test credit card account types map to CREDIT."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                {"id": "acc1", "iban": "BE123", "status": "READY"},
                {"account": {"iban": "BE123", "cashAccountType": "CARD", "currency": "EUR"}},
            ]

            account = await adapter.get_account_details("acc1")
            assert account.account_type == ProviderAccountType.CREDIT

    @pytest.mark.asyncio
    async def test_map_account_type_unknown(self, adapter) -> None:
        """Test unknown account type maps to OTHER."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                {"id": "acc1", "iban": "BE123", "status": "READY"},
                {"account": {"iban": "BE123", "cashAccountType": "UNKNOWN", "currency": "EUR"}},
            ]

            account = await adapter.get_account_details("acc1")
            assert account.account_type == ProviderAccountType.OTHER
