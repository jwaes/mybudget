"""
GoCardless Bank Account Data adapter.

Implements the BankProviderAdapter interface for GoCardless (formerly Nordigen)
Bank Account Data API. This enables PSD2-compliant bank connections across Europe.

API Documentation: https://developer.gocardless.com/bank-account-data/overview
"""
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx
import structlog

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
from mybudget.config import settings

logger = structlog.get_logger(__name__)


class GoCardlessError(Exception):
    """Base exception for GoCardless adapter errors."""

    pass


class GoCardlessAuthError(GoCardlessError):
    """Authentication error (invalid credentials or expired token)."""

    pass


class GoCardlessAPIError(GoCardlessError):
    """API error response from GoCardless."""

    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class GoCardlessRateLimitError(GoCardlessError):
    """Rate limit exceeded."""

    pass


# Account type mapping from GoCardless cashAccountType to our types
ACCOUNT_TYPE_MAP: dict[str, ProviderAccountType] = {
    "CACC": ProviderAccountType.CHECKING,  # Current Account
    "CASH": ProviderAccountType.CHECKING,  # Cash Account
    "CHAR": ProviderAccountType.CHECKING,  # Charges Account
    "CISH": ProviderAccountType.CHECKING,  # Cash Income Account
    "COMM": ProviderAccountType.CHECKING,  # Commission Account
    "CPAC": ProviderAccountType.CHECKING,  # Clearing Participant Account
    "LLSV": ProviderAccountType.SAVINGS,  # Limited Liquidity Savings Account
    "LOAN": ProviderAccountType.LOAN,  # Loan Account
    "MGLD": ProviderAccountType.INVESTMENT,  # Marginal Lending Account
    "MOMA": ProviderAccountType.INVESTMENT,  # Money Market Account
    "NREX": ProviderAccountType.OTHER,  # Non-Resident External Account
    "ODFT": ProviderAccountType.CHECKING,  # Overdraft Account
    "ONDP": ProviderAccountType.SAVINGS,  # Overnight Deposit Account
    "OTHR": ProviderAccountType.OTHER,  # Other Account
    "SACC": ProviderAccountType.CHECKING,  # Settlement Account
    "SLRY": ProviderAccountType.CHECKING,  # Salary Account
    "SVGS": ProviderAccountType.SAVINGS,  # Savings Account
    "TAXE": ProviderAccountType.OTHER,  # Tax Account
    "TRAN": ProviderAccountType.CHECKING,  # Transaction Account
    "TRAS": ProviderAccountType.CHECKING,  # Cash Trading Account
    "CARD": ProviderAccountType.CREDIT,  # Card Account (typically credit)
}


class GoCardlessAdapter(BankProviderAdapter):
    """
    GoCardless Bank Account Data adapter.

    Implements PSD2-compliant bank connections via the GoCardless (Nordigen) API.
    This adapter handles:
    - Institution discovery (banks available in each country)
    - OAuth-based bank authorization flow
    - Account and balance retrieval
    - Transaction synchronization
    """

    def __init__(self) -> None:
        """Initialize the GoCardless adapter.

        Raises:
            GoCardlessAuthError: If credentials are not configured.
        """
        if not settings.GOCARDLESS_SECRET_ID or not settings.GOCARDLESS_SECRET_KEY:
            raise GoCardlessAuthError(
                "GoCardless credentials not configured. "
                "Set GOCARDLESS_SECRET_ID and GOCARDLESS_SECRET_KEY environment variables."
            )

        self._base_url = settings.GOCARDLESS_BASE_URL.rstrip("/")
        self._secret_id = settings.GOCARDLESS_SECRET_ID
        self._secret_key = settings.GOCARDLESS_SECRET_KEY

        # Access token cache
        self._access_token: str | None = None
        self._token_expires: datetime | None = None

        # HTTP client with retry support
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return "gocardless"

    async def _get_access_token(self) -> str:
        """Get or refresh the access token.

        Returns:
            Valid access token.

        Raises:
            GoCardlessAuthError: If authentication fails.
        """
        # Check if current token is still valid (with 5-minute buffer)
        if (
            self._access_token
            and self._token_expires
            and datetime.now(UTC) < self._token_expires
        ):
            return self._access_token

        # Request new token
        try:
            response = await self._client.post(
                f"{self._base_url}/token/new/",
                json={
                    "secret_id": self._secret_id,
                    "secret_key": self._secret_key,
                },
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access"]
            # Token expires in access_expires seconds, subtract 5 minutes for safety
            expires_in = data.get("access_expires", 86400) - 300
            self._token_expires = datetime.now(UTC).replace(
                microsecond=0
            ) + __import__("datetime").timedelta(seconds=expires_in)

            logger.debug("GoCardless access token refreshed", expires_in=expires_in)
            return self._access_token

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise GoCardlessAuthError("Invalid GoCardless credentials") from e
            raise GoCardlessAPIError(
                f"Token request failed: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except Exception as e:
            raise GoCardlessAuthError(f"Failed to obtain access token: {e}") from e

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (will be appended to base URL)
            json: JSON body for POST/PUT requests
            params: Query parameters

        Returns:
            Parsed JSON response.

        Raises:
            GoCardlessAPIError: If the API returns an error.
            GoCardlessAuthError: If authentication fails.
            GoCardlessRateLimitError: If rate limited.
        """
        token = await self._get_access_token()

        # Clean up params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        url = f"{self._base_url}/{endpoint.lstrip('/')}"

        try:
            response = await self._client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}"},
                json=json,
                params=params,
            )
            response.raise_for_status()

            # DELETE requests may return empty response
            if response.status_code == 204 or not response.content:
                return None

            return response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code

            # Try to get error detail from response
            try:
                error_data = e.response.json()
                detail = error_data.get("detail") or error_data.get("summary") or str(error_data)
            except Exception:
                detail = e.response.text

            if status_code == 401:
                # Token may have expired, clear it and retry once
                self._access_token = None
                self._token_expires = None
                raise GoCardlessAuthError(f"Authentication failed: {detail}") from e
            elif status_code == 429:
                raise GoCardlessRateLimitError("Rate limit exceeded") from e
            else:
                raise GoCardlessAPIError(
                    f"API error: {detail}",
                    status_code=status_code,
                    detail=detail,
                ) from e

    async def get_institutions(
        self,
        country: str | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Institution]:
        """Get list of available banking institutions."""
        params: dict[str, Any] = {}
        if country:
            params["country"] = country

        data = await self._make_request("GET", "/institutions/", params=params)

        institutions = []
        for item in data:
            institutions.append(
                Institution(
                    id=item["id"],
                    name=item["name"],
                    bic=item.get("bic"),
                    logo_url=item.get("logo"),
                    countries=tuple(item.get("countries", [])),
                )
            )

        # Apply pagination locally since API doesn't support it directly
        return institutions[offset : offset + limit]

    async def get_institution(self, institution_id: str) -> Institution | None:
        """Get details for a specific institution."""
        try:
            data = await self._make_request("GET", f"/institutions/{institution_id}/")
            return Institution(
                id=data["id"],
                name=data["name"],
                bic=data.get("bic"),
                logo_url=data.get("logo"),
                countries=tuple(data.get("countries", [])),
            )
        except GoCardlessAPIError as e:
            if e.status_code == 404:
                return None
            raise

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
        """Create a requisition (authorization request) for bank access."""
        # First, create an end-user agreement
        agreement_data = await self._make_request(
            "POST",
            "/agreements/enduser/",
            json={
                "institution_id": institution_id,
                "access_valid_for_days": agreement_days,
                "max_historical_days": max_historical_days,
                "access_scope": ["balances", "details", "transactions"],
            },
        )

        agreement_id = agreement_data["id"]

        # Then create the requisition
        requisition_data = await self._make_request(
            "POST",
            "/requisitions/",
            json={
                "redirect": redirect_url,
                "institution_id": institution_id,
                "reference": reference,
                "agreement": agreement_id,
                "user_language": user_language,
            },
        )

        return RequisitionResponse(
            id=requisition_data["id"],
            link=requisition_data["link"],
            reference=requisition_data["reference"],
            status=requisition_data["status"],
        )

    async def get_requisition(self, requisition_id: str) -> AccountAccessResponse | None:
        """Get the status and details of a requisition."""
        try:
            data = await self._make_request("GET", f"/requisitions/{requisition_id}/")

            # Parse created date for access_valid_until estimation
            # GoCardless requisitions are valid for 90 days by default
            created = datetime.fromisoformat(data["created"].replace("Z", "+00:00"))
            access_valid_until = created + __import__("datetime").timedelta(days=90)

            return AccountAccessResponse(
                requisition_id=data["id"],
                accounts=data.get("accounts", []),
                institution_id=data["institution_id"],
                status=data["status"],
                access_valid_until=access_valid_until,
            )
        except GoCardlessAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_accounts(
        self,
        requisition_id: str,
    ) -> list[ProviderAccount]:
        """Get accounts linked to a requisition."""
        requisition = await self.get_requisition(requisition_id)
        if not requisition:
            return []

        accounts = []
        for account_id in requisition.accounts:
            account = await self.get_account_details(account_id)
            if account:
                accounts.append(account)

        return accounts

    async def get_account_details(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """Get details for a specific account."""
        try:
            # Get basic account info
            basic_data = await self._make_request("GET", f"/accounts/{account_id}/")

            # Get detailed account metadata
            details_data = await self._make_request("GET", f"/accounts/{account_id}/details/")
            account_info = details_data.get("account", {})

            # Map account type
            cash_account_type = account_info.get("cashAccountType", "")
            account_type = ACCOUNT_TYPE_MAP.get(cash_account_type, ProviderAccountType.OTHER)

            return ProviderAccount(
                id=basic_data["id"],
                name=account_info.get("name") or account_info.get("product"),
                iban=basic_data.get("iban") or account_info.get("iban"),
                account_number_masked=self._mask_iban(
                    basic_data.get("iban") or account_info.get("iban")
                ),
                account_type=account_type,
                currency=account_info.get("currency", "EUR"),
                owner_name=basic_data.get("owner_name") or account_info.get("ownerName"),
            )
        except GoCardlessAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_account_balances(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """Get current balance for an account."""
        try:
            # First get account details
            account = await self.get_account_details(account_id)
            if not account:
                return None

            # Then get balances
            balance_data = await self._make_request("GET", f"/accounts/{account_id}/balances/")
            balances = balance_data.get("balances", [])

            # Prefer interimAvailable, fall back to closingBooked
            balance_amount: Decimal | None = None
            balance_date: datetime | None = None

            for balance in balances:
                balance_type = balance.get("balanceType", "")
                if balance_type == "interimAvailable":
                    balance_amount = Decimal(balance["balanceAmount"]["amount"])
                    if ref_date := balance.get("referenceDate"):
                        balance_date = datetime.strptime(ref_date, "%Y-%m-%d").replace(
                            tzinfo=UTC
                        )
                    break
                elif balance_type == "closingBooked" and balance_amount is None:
                    balance_amount = Decimal(balance["balanceAmount"]["amount"])
                    if ref_date := balance.get("referenceDate"):
                        balance_date = datetime.strptime(ref_date, "%Y-%m-%d").replace(
                            tzinfo=UTC
                        )

            # Return updated account with balance
            return ProviderAccount(
                id=account.id,
                name=account.name,
                iban=account.iban,
                account_number_masked=account.account_number_masked,
                account_type=account.account_type,
                currency=account.currency,
                balance=balance_amount,
                balance_date=balance_date,
                owner_name=account.owner_name,
            )
        except GoCardlessAPIError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_transactions(
        self,
        account_id: str,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ProviderTransaction]:
        """Get transactions for an account."""
        params: dict[str, Any] = {}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        data = await self._make_request(
            "GET", f"/accounts/{account_id}/transactions/", params=params
        )

        transactions = []
        tx_data = data.get("transactions", {})

        # Process booked transactions
        for tx in tx_data.get("booked", []):
            transactions.append(self._parse_transaction(tx, ProviderTransactionStatus.BOOKED))

        # Process pending transactions
        for tx in tx_data.get("pending", []):
            transactions.append(self._parse_transaction(tx, ProviderTransactionStatus.PENDING))

        return transactions

    def _parse_transaction(
        self, tx: dict[str, Any], status: ProviderTransactionStatus
    ) -> ProviderTransaction:
        """Parse a transaction from GoCardless format."""
        amount_data = tx.get("transactionAmount", {})
        amount = Decimal(amount_data.get("amount", "0"))
        currency = amount_data.get("currency", "EUR")

        # Parse dates
        booking_date_str = tx.get("bookingDate")
        value_date_str = tx.get("valueDate")

        booking_date = (
            datetime.strptime(booking_date_str, "%Y-%m-%d").date()
            if booking_date_str
            else None
        )
        value_date = (
            datetime.strptime(value_date_str, "%Y-%m-%d").date() if value_date_str else None
        )

        # Use booking date as primary date, fall back to value date
        tx_date = booking_date or value_date or date.today()

        # Build description from available fields
        description = (
            tx.get("remittanceInformationUnstructured")
            or tx.get("remittanceInformationStructured")
            or tx.get("additionalInformation")
            or ""
        )

        return ProviderTransaction(
            id=tx.get("transactionId") or tx.get("internalTransactionId") or "",
            date=tx_date,
            amount=amount,
            currency=currency,
            description=description,
            status=status,
            creditor_name=tx.get("creditorName"),
            debtor_name=tx.get("debtorName"),
            reference=tx.get("endToEndId"),
            internal_reference=tx.get("internalTransactionId"),
            bank_transaction_code=tx.get("bankTransactionCode"),
            booking_date=booking_date,
            value_date=value_date,
        )

    async def refresh_access(
        self,
        requisition_id: str,
    ) -> AccountAccessResponse | None:
        """Refresh access token for a requisition if supported.

        Note: GoCardless handles token refresh internally through their OAuth flow.
        This method simply returns the current requisition status.
        """
        return await self.get_requisition(requisition_id)

    async def revoke_access(
        self,
        requisition_id: str,
    ) -> bool:
        """Revoke access and delete requisition."""
        try:
            await self._make_request("DELETE", f"/requisitions/{requisition_id}/")
            return True
        except GoCardlessAPIError as e:
            if e.status_code == 404:
                return False
            raise

    def _mask_iban(self, iban: str | None) -> str | None:
        """Mask IBAN for display, showing only last 4 characters."""
        if not iban or len(iban) < 4:
            return iban
        return f"****{iban[-4:]}"

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "GoCardlessAdapter":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()
