"""
EnableBanking adapter.

Implements the BankProviderAdapter interface for EnableBanking API.
This enables PSD2-compliant bank connections across Europe.

API Documentation: https://enablebanking.com/docs/api/reference
"""
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import jwt
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


class EnableBankingError(Exception):
    """Base exception for EnableBanking adapter errors."""

    pass


class EnableBankingAuthError(EnableBankingError):
    """Authentication error (invalid credentials or expired token)."""

    pass


class EnableBankingAPIError(EnableBankingError):
    """API error response from EnableBanking."""

    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class EnableBankingRateLimitError(EnableBankingError):
    """Rate limit exceeded."""

    pass


# Account type mapping from EnableBanking cashAccountType to our types
ACCOUNT_TYPE_MAP: dict[str, ProviderAccountType] = {
    "CACC": ProviderAccountType.CHECKING,
    "SVGS": ProviderAccountType.SAVINGS,
    "CARD": ProviderAccountType.CREDIT,
    "LOAN": ProviderAccountType.LOAN,
    "OTHR": ProviderAccountType.OTHER,
}


class EnableBankingAdapter(BankProviderAdapter):
    """
    EnableBanking adapter.

    Implements PSD2-compliant bank connections via the EnableBanking API.
    Uses JWT RS256 authentication with a private key.

    This adapter handles:
    - Institution discovery (ASPSPs - Account Servicing Payment Service Providers)
    - OAuth-based bank authorization flow
    - Account and balance retrieval
    - Transaction synchronization
    """

    def __init__(self) -> None:
        """Initialize the EnableBanking adapter.

        Raises:
            EnableBankingAuthError: If credentials are not configured.
        """
        if not settings.ENABLEBANKING_APP_ID:
            raise EnableBankingAuthError(
                "EnableBanking application ID not configured. "
                "Set ENABLEBANKING_APP_ID environment variable."
            )
        if not settings.ENABLEBANKING_PRIVATE_KEY_PATH:
            raise EnableBankingAuthError(
                "EnableBanking private key not configured. "
                "Set ENABLEBANKING_PRIVATE_KEY_PATH environment variable."
            )

        key_path = Path(settings.ENABLEBANKING_PRIVATE_KEY_PATH)
        if not key_path.exists():
            raise EnableBankingAuthError(
                f"EnableBanking private key file not found: {key_path}"
            )

        self._base_url = settings.ENABLEBANKING_BASE_URL.rstrip("/")
        self._app_id = settings.ENABLEBANKING_APP_ID
        self._private_key = key_path.read_text()

        # JWT token cache
        self._jwt_token: str | None = None
        self._token_expires: datetime | None = None

        # Session cache (session_id -> session data)
        self._session_cache: dict[str, dict[str, Any]] = {}

        # HTTP client
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return "enablebanking"

    def _generate_jwt(self) -> str:
        """Generate a JWT token for API authentication.

        Returns:
            JWT token string.
        """
        # Check if current token is still valid (with 5-minute buffer)
        if (
            self._jwt_token
            and self._token_expires
            and datetime.now(UTC) < self._token_expires
        ):
            return self._jwt_token

        # Generate new JWT
        now = datetime.now(UTC)
        expires = now + timedelta(hours=1)  # Token valid for 1 hour

        payload = {
            "iss": self._app_id,
            "aud": "enablebanking.com",
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }

        self._jwt_token = jwt.encode(
            payload,
            self._private_key,
            algorithm="RS256",
            headers={"kid": self._app_id},
        )
        self._token_expires = expires - timedelta(minutes=5)  # Add buffer

        logger.debug("EnableBanking JWT generated", expires_at=expires.isoformat())
        return self._jwt_token

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
            EnableBankingAPIError: If the API returns an error.
            EnableBankingAuthError: If authentication fails.
            EnableBankingRateLimitError: If rate limited.
        """
        token = self._generate_jwt()

        # Clean up params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        url = f"{self._base_url}/{endpoint.lstrip('/')}"

        try:
            response = await self._client.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
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
                detail = error_data.get("message") or error_data.get("error") or str(error_data)
            except Exception:
                detail = e.response.text

            if status_code == 401:
                # Clear token cache
                self._jwt_token = None
                self._token_expires = None
                raise EnableBankingAuthError(f"Authentication failed: {detail}") from e
            elif status_code == 429:
                raise EnableBankingRateLimitError("Rate limit exceeded") from e
            else:
                raise EnableBankingAPIError(
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
        """Get list of available banking institutions (ASPSPs)."""
        params: dict[str, Any] = {}
        if country:
            params["country"] = country

        data = await self._make_request("GET", "/aspsps", params=params)

        institutions = []
        aspsps = data.get("aspsps", []) if isinstance(data, dict) else data

        for item in aspsps:
            institutions.append(
                Institution(
                    id=item["name"],  # EnableBanking uses name as identifier
                    name=item.get("fullname", item["name"]),
                    bic=item.get("bic"),
                    logo_url=item.get("logo"),
                    countries=tuple(item.get("countries", [item.get("country", "")])),
                )
            )

        # Apply pagination
        return institutions[offset : offset + limit]

    async def get_institution(self, institution_id: str) -> Institution | None:
        """Get details for a specific institution."""
        # EnableBanking doesn't have a single-institution endpoint
        # Search in the list
        institutions = await self.get_institutions()
        for inst in institutions:
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
        """Create an authorization request for bank access."""
        # EnableBanking uses POST /auth to start OAuth
        data = await self._make_request(
            "POST",
            "/auth",
            json={
                "access": {
                    "valid_until": (
                        datetime.now(UTC) + timedelta(days=agreement_days)
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                "aspsp": {"name": institution_id},
                "state": reference,
                "redirect_url": redirect_url,
                "psu_type": "personal",
            },
        )

        return RequisitionResponse(
            id=data.get("auth_id", reference),  # auth_id from response or reference
            link=data["url"],  # Redirect URL for bank authentication
            reference=reference,
            status="CREATED",
        )

    async def get_requisition(self, requisition_id: str) -> AccountAccessResponse | None:
        """Get the status and details of an authorization."""
        # Check if we have a cached session for this requisition
        if requisition_id in self._session_cache:
            session = self._session_cache[requisition_id]
            accounts = [acc["account_id"]["iban"] for acc in session.get("accounts", [])]
            return AccountAccessResponse(
                requisition_id=requisition_id,
                accounts=accounts,
                institution_id=session.get("aspsp", {}).get("name", ""),
                status="LN",  # Linked
                access_valid_until=datetime.fromisoformat(
                    session["access"]["valid_until"].replace("Z", "+00:00")
                )
                if session.get("access", {}).get("valid_until")
                else None,
            )
        return None

    async def complete_authorization(
        self,
        auth_code: str,
    ) -> AccountAccessResponse:
        """Complete OAuth by exchanging code for session.

        This method is specific to EnableBanking's flow.
        Call this after the user returns from bank authentication.

        Args:
            auth_code: Authorization code from callback

        Returns:
            AccountAccessResponse with linked accounts
        """
        data = await self._make_request(
            "POST",
            "/sessions",
            json={"code": auth_code},
        )

        session_id = data["session_id"]

        # Cache the session
        self._session_cache[session_id] = data

        # Extract account IDs
        accounts = []
        for acc in data.get("accounts", []):
            account_id = acc.get("account_id", {})
            # Use IBAN or other identifier as account ID
            acc_id = account_id.get("iban") or account_id.get("other", {}).get("identification")
            if acc_id:
                accounts.append(acc_id)

        access_valid_until = None
        if data.get("access", {}).get("valid_until"):
            access_valid_until = datetime.fromisoformat(
                data["access"]["valid_until"].replace("Z", "+00:00")
            )

        return AccountAccessResponse(
            requisition_id=session_id,
            accounts=accounts,
            institution_id=data.get("aspsp", {}).get("name", ""),
            status="LN",  # Linked
            access_valid_until=access_valid_until,
        )

    async def get_accounts(
        self,
        requisition_id: str,
    ) -> list[ProviderAccount]:
        """Get accounts linked to a session."""
        session = self._session_cache.get(requisition_id)
        if not session:
            return []

        accounts = []
        for acc in session.get("accounts", []):
            account_id = acc.get("account_id", {})
            iban = account_id.get("iban")
            other_id = account_id.get("other", {}).get("identification")
            acc_id = iban or other_id or ""

            # Map account type
            account_type = ACCOUNT_TYPE_MAP.get(
                acc.get("cash_account_type", "OTHR"),
                ProviderAccountType.OTHER,
            )

            accounts.append(
                ProviderAccount(
                    id=acc_id,
                    name=acc.get("product") or acc.get("name"),
                    iban=iban,
                    account_number_masked=self._mask_iban(iban),
                    account_type=account_type,
                    currency=acc.get("currency", "EUR"),
                    owner_name=acc.get("owner_name"),
                )
            )

        return accounts

    async def get_account_details(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """Get details for a specific account."""
        # EnableBanking returns account details in session
        # Search through cached sessions
        for session in self._session_cache.values():
            for acc in session.get("accounts", []):
                account_id_data = acc.get("account_id", {})
                iban = account_id_data.get("iban")
                other_id = account_id_data.get("other", {}).get("identification")
                acc_id = iban or other_id or ""

                if acc_id == account_id:
                    account_type = ACCOUNT_TYPE_MAP.get(
                        acc.get("cash_account_type", "OTHR"),
                        ProviderAccountType.OTHER,
                    )

                    return ProviderAccount(
                        id=acc_id,
                        name=acc.get("product") or acc.get("name"),
                        iban=iban,
                        account_number_masked=self._mask_iban(iban),
                        account_type=account_type,
                        currency=acc.get("currency", "EUR"),
                        owner_name=acc.get("owner_name"),
                    )
        return None

    async def get_account_balances(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """Get current balance for an account."""
        # Find the session that contains this account
        session_id = None
        for sid, session in self._session_cache.items():
            for acc in session.get("accounts", []):
                account_id_data = acc.get("account_id", {})
                iban = account_id_data.get("iban")
                other_id = account_id_data.get("other", {}).get("identification")
                if (iban or other_id) == account_id:
                    session_id = sid
                    break
            if session_id:
                break

        if not session_id:
            return None

        # Fetch balances from API
        try:
            data = await self._make_request(
                "GET",
                f"/accounts/{account_id}/balances",
                params={"session_id": session_id},
            )
        except EnableBankingAPIError as e:
            if e.status_code == 404:
                return None
            raise

        # Get account details first
        account = await self.get_account_details(account_id)
        if not account:
            return None

        # Parse balances - prefer available balance
        balance_amount: Decimal | None = None
        balance_date: datetime | None = None

        for balance in data.get("balances", []):
            balance_type = balance.get("balance_type", "")
            if balance_type in ("interimAvailable", "available"):
                balance_amount = Decimal(str(balance.get("balance_amount", {}).get("amount", 0)))
                if ref_date := balance.get("reference_date"):
                    balance_date = datetime.fromisoformat(ref_date.replace("Z", "+00:00"))
                break
            elif balance_type in ("closingBooked", "booked") and balance_amount is None:
                balance_amount = Decimal(str(balance.get("balance_amount", {}).get("amount", 0)))
                if ref_date := balance.get("reference_date"):
                    balance_date = datetime.fromisoformat(ref_date.replace("Z", "+00:00"))

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

    async def get_transactions(
        self,
        account_id: str,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ProviderTransaction]:
        """Get transactions for an account."""
        # Find the session that contains this account
        session_id = None
        for sid, session in self._session_cache.items():
            for acc in session.get("accounts", []):
                account_id_data = acc.get("account_id", {})
                iban = account_id_data.get("iban")
                other_id = account_id_data.get("other", {}).get("identification")
                if (iban or other_id) == account_id:
                    session_id = sid
                    break
            if session_id:
                break

        if not session_id:
            return []

        params: dict[str, Any] = {"session_id": session_id}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        data = await self._make_request(
            "GET",
            f"/accounts/{account_id}/transactions",
            params=params,
        )

        transactions = []

        # Process transactions
        for tx in data.get("transactions", []):
            transactions.append(
                self._parse_transaction(tx, ProviderTransactionStatus.BOOKED)
            )

        # Process pending transactions if available
        for tx in data.get("pending_transactions", []):
            transactions.append(
                self._parse_transaction(tx, ProviderTransactionStatus.PENDING)
            )

        return transactions

    def _parse_transaction(
        self, tx: dict[str, Any], status: ProviderTransactionStatus
    ) -> ProviderTransaction:
        """Parse a transaction from EnableBanking format."""
        amount_data = tx.get("transaction_amount", {})
        amount = Decimal(str(amount_data.get("amount", 0)))
        currency = amount_data.get("currency", "EUR")

        # Parse dates
        booking_date_str = tx.get("booking_date")
        value_date_str = tx.get("value_date")

        booking_date = (
            datetime.strptime(booking_date_str, "%Y-%m-%d").date()
            if booking_date_str
            else None
        )
        value_date = (
            datetime.strptime(value_date_str, "%Y-%m-%d").date()
            if value_date_str
            else None
        )

        # Use booking date as primary date
        tx_date = booking_date or value_date or date.today()

        # Build description
        description = (
            tx.get("remittance_information_unstructured")
            or tx.get("remittance_information")
            or tx.get("additional_information")
            or ""
        )
        # Handle list of remittance info
        if isinstance(description, list):
            description = " ".join(description)

        return ProviderTransaction(
            id=tx.get("entry_reference") or tx.get("transaction_id") or "",
            date=tx_date,
            amount=amount,
            currency=currency,
            description=description,
            status=status,
            creditor_name=tx.get("creditor", {}).get("name") if tx.get("creditor") else None,
            debtor_name=tx.get("debtor", {}).get("name") if tx.get("debtor") else None,
            reference=tx.get("end_to_end_id"),
            internal_reference=tx.get("entry_reference"),
            bank_transaction_code=tx.get("proprietary_bank_transaction_code"),
            booking_date=booking_date,
            value_date=value_date,
        )

    async def refresh_access(
        self,
        requisition_id: str,
    ) -> AccountAccessResponse | None:
        """Refresh access for a session.

        EnableBanking sessions don't support refresh - user must re-authenticate.
        """
        return await self.get_requisition(requisition_id)

    async def revoke_access(
        self,
        requisition_id: str,
    ) -> bool:
        """Revoke access and delete session."""
        try:
            await self._make_request("DELETE", f"/sessions/{requisition_id}")
            # Remove from cache
            self._session_cache.pop(requisition_id, None)
            return True
        except EnableBankingAPIError as e:
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

    async def __aenter__(self) -> "EnableBankingAdapter":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()
