"""
Bank connection service for managing bank integrations.

This service handles the lifecycle of bank connections including:
- OAuth flow initiation and completion
- Connection listing and retrieval
- Disconnection and access revocation
- Institution search
"""
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mybudget.adapters.base import BankProviderAdapter
from mybudget.adapters.types import ProviderAccountType
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    LinkedAccountType,
    SyncJob,
    SyncJobStatus,
    SyncTriggerType,
)
from mybudget.schemas.bank_connection import (
    BankConnectionResponse,
    BankConnectionWithAccountsResponse,
    InstitutionResponse,
    LinkedAccountResponse,
    OAuthInitResponse,
)


def _map_account_type(provider_type: ProviderAccountType) -> LinkedAccountType | None:
    """Map provider account type to internal linked account type."""
    mapping = {
        ProviderAccountType.CHECKING: LinkedAccountType.CHECKING,
        ProviderAccountType.SAVINGS: LinkedAccountType.SAVINGS,
        ProviderAccountType.CREDIT: LinkedAccountType.CREDIT,
    }
    return mapping.get(provider_type)


class BankConnectionService:
    """Service for bank connection operations."""

    def __init__(self, db: AsyncSession, adapter: BankProviderAdapter):
        """
        Initialize with database session and bank provider adapter.

        Args:
            db: Async database session
            adapter: Bank provider adapter (GoCardless, Mock, etc.)
        """
        self.db = db
        self.adapter = adapter

    async def initiate_connection(
        self,
        user_id: UUID,
        institution_id: str,
        redirect_url: str,
    ) -> OAuthInitResponse:
        """
        Initiate a new bank connection via OAuth.

        Creates a requisition with the bank provider and a pending
        BankConnection record in the database.

        Args:
            user_id: User initiating the connection
            institution_id: Provider's institution ID
            redirect_url: URL to redirect after OAuth

        Returns:
            OAuthInitResponse with authorization URL and reference ID

        Raises:
            RuntimeError: If institution not found or requisition creation fails
        """
        # Get institution details from adapter
        institution = await self.adapter.get_institution(institution_id)
        if not institution:
            raise ValueError(f"Institution not found: {institution_id}")

        # Generate unique reference for tracking
        reference = str(uuid4())

        # Create requisition with provider
        requisition = await self.adapter.create_requisition(
            institution_id=institution_id,
            redirect_url=redirect_url,
            reference=reference,
        )

        # Create pending bank connection record
        connection = BankConnection(
            user_id=user_id,
            provider=self.adapter.provider_name,
            provider_connection_id=requisition.id,
            institution_id=institution_id,
            institution_name=institution.name,
            status=BankConnectionStatus.PENDING,
        )

        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)

        return OAuthInitResponse(
            authorization_url=requisition.link,
            reference_id=reference,
        )

    async def complete_oauth(
        self,
        user_id: UUID,
        reference_id: str,  # noqa: ARG002 - kept for API compatibility
    ) -> BankConnectionWithAccountsResponse:
        """
        Complete OAuth flow and activate the bank connection.

        Fetches linked accounts from the provider and stores them.
        Creates an initial sync job.

        Args:
            user_id: User completing the OAuth flow
            reference_id: Reference ID from OAuth initiation

        Returns:
            BankConnectionWithAccountsResponse with connection and accounts

        Raises:
            ValueError: If connection not found or not owned by user
        """
        # Find the pending connection by provider_connection_id pattern
        # The reference_id was used as the reference in create_requisition
        # We need to find connections for this user that are pending
        stmt = select(BankConnection).where(
            BankConnection.user_id == user_id,
            BankConnection.status == BankConnectionStatus.PENDING,
        )
        result = await self.db.execute(stmt)
        connections = list(result.scalars().all())

        # Find connection matching the requisition
        connection = None
        requisition_status = None
        for conn in connections:
            status = await self.adapter.get_requisition(conn.provider_connection_id)
            if (
                status
                and status.requisition_id == conn.provider_connection_id
                and status.status == "LN"  # Linked status
            ):
                connection = conn
                requisition_status = status
                break

        if not connection or not requisition_status:
            raise ValueError("No pending connection found or OAuth not completed")

        # Update connection status and access expiry
        connection.status = BankConnectionStatus.ACTIVE
        connection.access_valid_until = requisition_status.access_valid_until

        # Fetch and store linked accounts
        provider_accounts = await self.adapter.get_accounts(
            connection.provider_connection_id
        )

        linked_accounts = []
        for prov_acc in provider_accounts:
            linked_account = LinkedAccount(
                connection_id=connection.id,
                provider_account_id=prov_acc.id,
                account_name=prov_acc.name,
                account_number_masked=prov_acc.account_number_masked,
                account_type=_map_account_type(prov_acc.account_type),
                currency=prov_acc.currency,
                balance=prov_acc.balance,
                balance_updated_at=prov_acc.balance_date,
                is_active=True,
            )
            self.db.add(linked_account)
            linked_accounts.append(linked_account)

        # Schedule initial sync job
        sync_job = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.PENDING,
            trigger_type=SyncTriggerType.INITIAL,
        )
        self.db.add(sync_job)

        await self.db.commit()
        await self.db.refresh(connection)

        # Refresh linked accounts to get their IDs
        for la in linked_accounts:
            await self.db.refresh(la)

        return BankConnectionWithAccountsResponse(
            id=connection.id,
            user_id=connection.user_id,
            provider=connection.provider,
            institution_id=connection.institution_id,
            institution_name=connection.institution_name,
            status=connection.status,
            status_detail=connection.status_detail,
            last_sync_at=connection.last_sync_at,
            next_sync_at=connection.next_sync_at,
            access_valid_until=connection.access_valid_until,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
            linked_accounts=[
                LinkedAccountResponse.model_validate(la) for la in linked_accounts
            ],
        )

    async def list_connections(
        self,
        user_id: UUID,
    ) -> list[BankConnectionResponse]:
        """
        List all bank connections for a user.

        Args:
            user_id: User ID

        Returns:
            List of BankConnectionResponse objects
        """
        stmt = (
            select(BankConnection)
            .where(BankConnection.user_id == user_id)
            .order_by(BankConnection.created_at.desc())
        )
        result = await self.db.execute(stmt)
        connections = list(result.scalars().all())

        return [BankConnectionResponse.model_validate(conn) for conn in connections]

    async def get_connection(
        self,
        user_id: UUID,
        connection_id: UUID,
    ) -> BankConnectionWithAccountsResponse | None:
        """
        Get a bank connection with its linked accounts.

        Args:
            user_id: User ID (for access control)
            connection_id: Connection ID

        Returns:
            BankConnectionWithAccountsResponse if found, None otherwise
        """
        stmt = (
            select(BankConnection)
            .options(selectinload(BankConnection.linked_accounts))
            .where(
                BankConnection.id == connection_id,
                BankConnection.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            return None

        return BankConnectionWithAccountsResponse(
            id=connection.id,
            user_id=connection.user_id,
            provider=connection.provider,
            institution_id=connection.institution_id,
            institution_name=connection.institution_name,
            status=connection.status,
            status_detail=connection.status_detail,
            last_sync_at=connection.last_sync_at,
            next_sync_at=connection.next_sync_at,
            access_valid_until=connection.access_valid_until,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
            linked_accounts=[
                LinkedAccountResponse.model_validate(la)
                for la in connection.linked_accounts
            ],
        )

    async def disconnect(
        self,
        user_id: UUID,
        connection_id: UUID,
    ) -> bool:
        """
        Disconnect a bank connection and revoke access.

        Args:
            user_id: User ID (for access control)
            connection_id: Connection ID

        Returns:
            True if disconnected, False if not found
        """
        stmt = (
            select(BankConnection)
            .options(selectinload(BankConnection.linked_accounts))
            .where(
                BankConnection.id == connection_id,
                BankConnection.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            return False

        # Revoke access via adapter
        await self.adapter.revoke_access(connection.provider_connection_id)

        # Update connection status
        connection.status = BankConnectionStatus.DISCONNECTED
        connection.status_detail = "Disconnected by user"

        # Deactivate linked accounts
        for linked_account in connection.linked_accounts:
            linked_account.is_active = False

        await self.db.commit()

        return True

    async def get_institutions(
        self,
        country: str | None = None,
    ) -> list[InstitutionResponse]:
        """
        Get available banking institutions.

        Args:
            country: ISO 3166-1 alpha-2 country code to filter by

        Returns:
            List of InstitutionResponse objects
        """
        institutions = await self.adapter.get_institutions(country=country)

        return [
            InstitutionResponse(
                id=inst.id,
                name=inst.name,
                bic=inst.bic,
                logo_url=inst.logo_url,
                countries=list(inst.countries),
            )
            for inst in institutions
        ]
