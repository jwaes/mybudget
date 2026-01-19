"""
Abstract base class for bank provider adapters.

This defines the interface that all bank providers must implement,
enabling a provider-agnostic architecture for bank feed integration.
"""
from abc import ABC, abstractmethod
from datetime import date, datetime

from mybudget.adapters.types import (
    AccountAccessResponse,
    Institution,
    ProviderAccount,
    ProviderTransaction,
    RequisitionResponse,
)


class BankProviderAdapter(ABC):
    """Abstract base class for bank provider adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'gocardless')."""
        ...

    @abstractmethod
    async def get_institutions(
        self,
        country: str | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Institution]:
        """
        Get list of available banking institutions.

        Args:
            country: ISO 3166-1 alpha-2 country code to filter by (e.g., 'BE', 'NL')
            limit: Maximum number of institutions to return
            offset: Number of institutions to skip for pagination

        Returns:
            List of Institution objects
        """
        ...

    @abstractmethod
    async def get_institution(self, institution_id: str) -> Institution | None:
        """
        Get details for a specific institution.

        Args:
            institution_id: Provider's institution ID

        Returns:
            Institution details or None if not found
        """
        ...

    @abstractmethod
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
        """
        Create a requisition (authorization request) for bank access.

        Args:
            institution_id: Provider's institution ID
            redirect_url: URL to redirect user after bank authentication
            reference: Internal reference to track this requisition
            user_language: ISO 639-1 language code for bank auth pages
            agreement_days: Number of days the access agreement is valid
            max_historical_days: Days of transaction history to request

        Returns:
            RequisitionResponse with link for user to complete authorization
        """
        ...

    @abstractmethod
    async def get_requisition(self, requisition_id: str) -> AccountAccessResponse | None:
        """
        Get the status and details of a requisition.

        Args:
            requisition_id: Provider's requisition ID

        Returns:
            AccountAccessResponse with linked accounts, or None if not found
        """
        ...

    @abstractmethod
    async def get_accounts(
        self,
        requisition_id: str,
    ) -> list[ProviderAccount]:
        """
        Get accounts linked to a requisition.

        Args:
            requisition_id: Provider's requisition ID

        Returns:
            List of ProviderAccount objects
        """
        ...

    @abstractmethod
    async def get_account_details(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """
        Get details for a specific account.

        Args:
            account_id: Provider's account ID

        Returns:
            ProviderAccount details or None if not found
        """
        ...

    @abstractmethod
    async def get_account_balances(
        self,
        account_id: str,
    ) -> ProviderAccount | None:
        """
        Get current balance for an account.

        Args:
            account_id: Provider's account ID

        Returns:
            ProviderAccount with updated balance or None if not found
        """
        ...

    @abstractmethod
    async def get_transactions(
        self,
        account_id: str,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[ProviderTransaction]:
        """
        Get transactions for an account.

        Args:
            account_id: Provider's account ID
            date_from: Start date for transactions (inclusive)
            date_to: End date for transactions (inclusive)

        Returns:
            List of ProviderTransaction objects
        """
        ...

    @abstractmethod
    async def refresh_access(
        self,
        requisition_id: str,
    ) -> AccountAccessResponse | None:
        """
        Refresh access token for a requisition if supported.

        Args:
            requisition_id: Provider's requisition ID

        Returns:
            Updated AccountAccessResponse or None if refresh not supported/failed
        """
        ...

    @abstractmethod
    async def revoke_access(
        self,
        requisition_id: str,
    ) -> bool:
        """
        Revoke access and delete requisition.

        Args:
            requisition_id: Provider's requisition ID

        Returns:
            True if successfully revoked, False otherwise
        """
        ...

    async def health_check(self) -> bool:
        """
        Check if the provider API is accessible.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Default implementation tries to list institutions
            await self.get_institutions(limit=1)
            return True
        except Exception:
            return False
