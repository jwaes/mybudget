"""
Unit tests for EnableBanking adapter.

Uses mocked HTTP responses to test the adapter without hitting the real API.
"""
from datetime import date, datetime, timedelta, UTC
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile

import httpx
import pytest

from mybudget.adapters.enablebanking_adapter import (
    EnableBankingAdapter,
    EnableBankingAPIError,
    EnableBankingAuthError,
    EnableBankingRateLimitError,
)
from mybudget.adapters.types import (
    ProviderAccountType,
    ProviderTransactionStatus,
)


# Sample API responses based on EnableBanking API documentation
SAMPLE_ASPSPS_RESPONSE = {
    "aspsps": [
        {
            "name": "Nordea Personal",
            "fullname": "Nordea Personal Banking",
            "bic": "NDEAFIHH",
            "logo": "https://enablebanking.com/logos/nordea.png",
            "country": "FI",
            "countries": ["FI", "SE", "DK", "NO"],
        },
        {
            "name": "SEB",
            "fullname": "SEB Bank",
            "bic": "ESSESESS",
            "logo": "https://enablebanking.com/logos/seb.png",
            "country": "SE",
            "countries": ["SE"],
        },
    ]
}

SAMPLE_AUTH_RESPONSE = {
    "auth_id": "auth-123-456",
    "url": "https://api.enablebanking.com/auth?id=auth-123-456",
}

SAMPLE_SESSION_RESPONSE = {
    "session_id": "session-789-012",
    "access": {
        "valid_until": (datetime.now(UTC) + timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    },
    "aspsp": {
        "name": "Nordea Personal",
        "country": "FI",
    },
    "accounts": [
        {
            "account_id": {
                "iban": "FI4250001510000023",
            },
            "product": "Current Account",
            "currency": "EUR",
            "cash_account_type": "CACC",
            "owner_name": "John Doe",
        },
        {
            "account_id": {
                "iban": "FI9780001500000056",
            },
            "product": "Savings Account",
            "currency": "EUR",
            "cash_account_type": "SVGS",
            "owner_name": "John Doe",
        },
    ],
}

SAMPLE_BALANCES_RESPONSE = {
    "balances": [
        {
            "balance_amount": {"amount": "1500.50", "currency": "EUR"},
            "balance_type": "interimAvailable",
            "reference_date": "2024-01-15T12:00:00Z",
        },
        {
            "balance_amount": {"amount": "1400.00", "currency": "EUR"},
            "balance_type": "closingBooked",
            "reference_date": "2024-01-14T23:59:59Z",
        },
    ]
}

SAMPLE_TRANSACTIONS_RESPONSE = {
    "transactions": [
        {
            "entry_reference": "TX2024011500001",
            "booking_date": "2024-01-15",
            "value_date": "2024-01-15",
            "transaction_amount": {"amount": "-45.50", "currency": "EUR"},
            "creditor": {"name": "Supermarket ABC"},
            "remittance_information_unstructured": "Weekly groceries",
            "proprietary_bank_transaction_code": "PURCHASE",
        },
        {
            "entry_reference": "TX2024011400002",
            "booking_date": "2024-01-14",
            "value_date": "2024-01-14",
            "transaction_amount": {"amount": "3200.00", "currency": "EUR"},
            "debtor": {"name": "Acme Corp"},
            "remittance_information_unstructured": "Salary payment",
            "proprietary_bank_transaction_code": "SALARY",
        },
    ],
    "pending_transactions": [
        {
            "entry_reference": "TX2024011600001",
            "value_date": "2024-01-16",
            "transaction_amount": {"amount": "-15.00", "currency": "EUR"},
            "creditor": {"name": "Coffee House"},
            "remittance_information_unstructured": "Morning coffee",
        },
    ],
}


@pytest.fixture
def mock_private_key():
    """Create a temporary private key file for testing."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    # Generate a proper RSA key for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False) as f:
        f.write(key_bytes)
        return Path(f.name)


@pytest.fixture
def mock_settings(mock_private_key):
    """Mock settings for EnableBanking configuration."""
    with patch("mybudget.adapters.enablebanking_adapter.settings") as mock:
        mock.ENABLEBANKING_APP_ID = "test-app-id"
        mock.ENABLEBANKING_PRIVATE_KEY_PATH = str(mock_private_key)
        mock.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"
        yield mock


@pytest.fixture
def adapter(mock_settings, mock_private_key):
    """Create EnableBanking adapter instance."""
    return EnableBankingAdapter()


class TestEnableBankingAdapterBasics:
    """Tests for EnableBankingAdapter basic functionality."""

    def test_provider_name(self, adapter) -> None:
        """Test provider name returns 'enablebanking'."""
        assert adapter.provider_name == "enablebanking"

    def test_adapter_requires_app_id(self, mock_private_key) -> None:
        """Test adapter raises error without app ID."""
        with patch("mybudget.adapters.enablebanking_adapter.settings") as mock:
            mock.ENABLEBANKING_APP_ID = None
            mock.ENABLEBANKING_PRIVATE_KEY_PATH = str(mock_private_key)
            mock.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

            with pytest.raises(EnableBankingAuthError, match="application ID"):
                EnableBankingAdapter()

    def test_adapter_requires_private_key_path(self) -> None:
        """Test adapter raises error without private key path."""
        with patch("mybudget.adapters.enablebanking_adapter.settings") as mock:
            mock.ENABLEBANKING_APP_ID = "test-app-id"
            mock.ENABLEBANKING_PRIVATE_KEY_PATH = None
            mock.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

            with pytest.raises(EnableBankingAuthError, match="private key"):
                EnableBankingAdapter()

    def test_adapter_requires_private_key_file_exists(self) -> None:
        """Test adapter raises error if private key file doesn't exist."""
        with patch("mybudget.adapters.enablebanking_adapter.settings") as mock:
            mock.ENABLEBANKING_APP_ID = "test-app-id"
            mock.ENABLEBANKING_PRIVATE_KEY_PATH = "/nonexistent/path/key.pem"
            mock.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

            with pytest.raises(EnableBankingAuthError, match="not found"):
                EnableBankingAdapter()


class TestEnableBankingAdapterJWT:
    """Tests for JWT generation."""

    def test_generate_jwt(self, adapter) -> None:
        """Test JWT token generation."""
        token = adapter._generate_jwt()

        assert token is not None
        assert isinstance(token, str)
        # JWT has 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_jwt_caching(self, adapter) -> None:
        """Test JWT token is cached and reused."""
        token1 = adapter._generate_jwt()
        token2 = adapter._generate_jwt()

        assert token1 == token2


class TestEnableBankingAdapterInstitutions:
    """Tests for institution-related methods."""

    @pytest.mark.asyncio
    async def test_get_institutions(self, adapter) -> None:
        """Test getting list of institutions (ASPSPs)."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_ASPSPS_RESPONSE

            institutions = await adapter.get_institutions()

            assert len(institutions) == 2
            assert institutions[0].id == "Nordea Personal"
            assert institutions[0].name == "Nordea Personal Banking"
            assert institutions[0].bic == "NDEAFIHH"
            assert "FI" in institutions[0].countries
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_institutions_by_country(self, adapter) -> None:
        """Test filtering institutions by country."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"aspsps": [SAMPLE_ASPSPS_RESPONSE["aspsps"][1]]}

            institutions = await adapter.get_institutions(country="SE")

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["params"]["country"] == "SE"

    @pytest.mark.asyncio
    async def test_get_institution_by_id(self, adapter) -> None:
        """Test getting a specific institution."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_ASPSPS_RESPONSE

            institution = await adapter.get_institution("Nordea Personal")

            assert institution is not None
            assert institution.id == "Nordea Personal"
            assert institution.name == "Nordea Personal Banking"

    @pytest.mark.asyncio
    async def test_get_institution_not_found(self, adapter) -> None:
        """Test getting non-existent institution returns None."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_ASPSPS_RESPONSE

            institution = await adapter.get_institution("NONEXISTENT")

            assert institution is None


class TestEnableBankingAdapterAuthorization:
    """Tests for authorization handling."""

    @pytest.mark.asyncio
    async def test_create_requisition(self, adapter) -> None:
        """Test creating an authorization (requisition)."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_AUTH_RESPONSE

            requisition = await adapter.create_requisition(
                institution_id="Nordea Personal",
                redirect_url="https://myapp.com/callback",
                reference="user-123-req-1",
            )

            assert requisition.id == "auth-123-456"
            assert "enablebanking.com" in requisition.link
            assert requisition.reference == "user-123-req-1"
            assert requisition.status == "CREATED"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_authorization(self, adapter) -> None:
        """Test completing OAuth flow with session creation."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE

            result = await adapter.complete_authorization("auth-code-xyz")

            assert result.requisition_id == "session-789-012"
            assert len(result.accounts) == 2
            assert result.institution_id == "Nordea Personal"
            assert result.status == "LN"
            assert result.access_valid_until is not None

    @pytest.mark.asyncio
    async def test_get_requisition_with_cached_session(self, adapter) -> None:
        """Test getting requisition when session is cached."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        # Now get_requisition should return cached data
        result = await adapter.get_requisition("session-789-012")

        assert result is not None
        assert result.requisition_id == "session-789-012"
        assert result.status == "LN"

    @pytest.mark.asyncio
    async def test_get_requisition_not_cached(self, adapter) -> None:
        """Test getting requisition when session is not cached."""
        result = await adapter.get_requisition("unknown-session")

        assert result is None


class TestEnableBankingAdapterAccounts:
    """Tests for account handling."""

    @pytest.mark.asyncio
    async def test_get_accounts(self, adapter) -> None:
        """Test getting accounts from session."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        accounts = await adapter.get_accounts("session-789-012")

        assert len(accounts) == 2
        assert accounts[0].id == "FI4250001510000023"
        assert accounts[0].iban == "FI4250001510000023"
        assert accounts[0].account_type == ProviderAccountType.CHECKING
        assert accounts[0].currency == "EUR"
        assert accounts[0].owner_name == "John Doe"

        assert accounts[1].id == "FI9780001500000056"
        assert accounts[1].account_type == ProviderAccountType.SAVINGS

    @pytest.mark.asyncio
    async def test_get_accounts_no_session(self, adapter) -> None:
        """Test getting accounts when session not cached."""
        accounts = await adapter.get_accounts("unknown-session")

        assert accounts == []

    @pytest.mark.asyncio
    async def test_get_account_details(self, adapter) -> None:
        """Test getting account details."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        account = await adapter.get_account_details("FI4250001510000023")

        assert account is not None
        assert account.id == "FI4250001510000023"
        assert account.iban == "FI4250001510000023"
        assert account.account_type == ProviderAccountType.CHECKING

    @pytest.mark.asyncio
    async def test_get_account_details_not_found(self, adapter) -> None:
        """Test getting non-existent account returns None."""
        account = await adapter.get_account_details("NONEXISTENT")

        assert account is None

    @pytest.mark.asyncio
    async def test_get_account_balances(self, adapter) -> None:
        """Test getting account balances."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [
                SAMPLE_SESSION_RESPONSE,
                SAMPLE_BALANCES_RESPONSE,
            ]
            await adapter.complete_authorization("auth-code-xyz")

        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_BALANCES_RESPONSE

            account = await adapter.get_account_balances("FI4250001510000023")

            assert account is not None
            assert account.balance == Decimal("1500.50")
            assert account.balance_date is not None


class TestEnableBankingAdapterTransactions:
    """Tests for transaction handling."""

    @pytest.mark.asyncio
    async def test_get_transactions(self, adapter) -> None:
        """Test getting transactions."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_TRANSACTIONS_RESPONSE

            transactions = await adapter.get_transactions("FI4250001510000023")

            assert len(transactions) == 3  # 2 booked + 1 pending

            # Check booked transactions
            assert transactions[0].id == "TX2024011500001"
            assert transactions[0].amount == Decimal("-45.50")
            assert transactions[0].status == ProviderTransactionStatus.BOOKED
            assert transactions[0].creditor_name == "Supermarket ABC"

            assert transactions[1].id == "TX2024011400002"
            assert transactions[1].amount == Decimal("3200.00")
            assert transactions[1].debtor_name == "Acme Corp"

            # Check pending transaction
            assert transactions[2].id == "TX2024011600001"
            assert transactions[2].status == ProviderTransactionStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_transactions_with_date_filter(self, adapter) -> None:
        """Test getting transactions with date filter."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_TRANSACTIONS_RESPONSE

            await adapter.get_transactions(
                "FI4250001510000023",
                date_from=date(2024, 1, 1),
                date_to=date(2024, 1, 31),
            )

            call_args = mock_request.call_args
            assert call_args[1]["params"]["date_from"] == "2024-01-01"
            assert call_args[1]["params"]["date_to"] == "2024-01-31"

    @pytest.mark.asyncio
    async def test_get_transactions_no_session(self, adapter) -> None:
        """Test getting transactions when session not cached."""
        transactions = await adapter.get_transactions("unknown-account")

        assert transactions == []


class TestEnableBankingAdapterAccessManagement:
    """Tests for access management."""

    @pytest.mark.asyncio
    async def test_refresh_access(self, adapter) -> None:
        """Test refresh access returns current requisition status."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        result = await adapter.refresh_access("session-789-012")

        # Should return cached session data
        assert result is not None
        assert result.requisition_id == "session-789-012"

    @pytest.mark.asyncio
    async def test_revoke_access(self, adapter) -> None:
        """Test revoking access."""
        # First complete authorization to cache session
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = SAMPLE_SESSION_RESPONSE
            await adapter.complete_authorization("auth-code-xyz")

        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await adapter.revoke_access("session-789-012")

            assert result is True
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_access_not_found(self, adapter) -> None:
        """Test revoking non-existent session."""
        with patch.object(adapter, "_make_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = EnableBankingAPIError("Not found", status_code=404)

            result = await adapter.revoke_access("unknown-session")

            assert result is False


class TestEnableBankingAdapterErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self, adapter) -> None:
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_response.text = "Internal server error"
        mock_response.content = b"error"

        http_error = httpx.HTTPStatusError(
            "500 Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_response.raise_for_status.side_effect = http_error

        with patch.object(adapter._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(EnableBankingAPIError) as exc_info:
                await adapter._make_request("GET", "/test")

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_auth_error_handling(self, adapter) -> None:
        """Test authentication error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_response.text = "Unauthorized"
        mock_response.content = b"error"

        http_error = httpx.HTTPStatusError(
            "401 Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_response.raise_for_status.side_effect = http_error

        with patch.object(adapter._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(EnableBankingAuthError):
                await adapter._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, adapter) -> None:
        """Test rate limit error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_response.text = "Rate limit exceeded"
        mock_response.content = b"error"

        http_error = httpx.HTTPStatusError(
            "429 Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_response.raise_for_status.side_effect = http_error

        with patch.object(adapter._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(EnableBankingRateLimitError):
                await adapter._make_request("GET", "/test")


class TestEnableBankingAdapterContextManager:
    """Tests for context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_settings, mock_private_key) -> None:
        """Test async context manager."""
        async with EnableBankingAdapter() as adapter:
            assert adapter.provider_name == "enablebanking"


class TestEnableBankingAdapterUtilities:
    """Tests for utility methods."""

    def test_mask_iban(self, adapter) -> None:
        """Test IBAN masking."""
        assert adapter._mask_iban("FI4250001510000023") == "****0023"
        assert adapter._mask_iban("BE68") == "****BE68"
        assert adapter._mask_iban("AB") == "AB"
        assert adapter._mask_iban(None) is None
