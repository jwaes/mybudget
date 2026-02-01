"""
Bank connection service for managing bank integrations.

This service handles the lifecycle of bank connections including:
- OAuth flow initiation and completion
- Connection listing and retrieval
- Disconnection and access revocation
- Institution search
- Connection health monitoring and re-authentication
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mybudget.adapters.base import BankProviderAdapter
from mybudget.adapters.types import ProviderAccountType
from mybudget.models.account import Account, AccountType, SyncStatus
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
    ConnectionHealthStatus,
    InstitutionResponse,
    LinkedAccountResponse,
    OAuthInitResponse,
)


def _map_linked_account_type(provider_type: ProviderAccountType) -> LinkedAccountType | None:
    """Map provider account type to linked account type."""
    mapping = {
        ProviderAccountType.CHECKING: LinkedAccountType.CHECKING,
        ProviderAccountType.SAVINGS: LinkedAccountType.SAVINGS,
        ProviderAccountType.CREDIT: LinkedAccountType.CREDIT,
    }
    return mapping.get(provider_type)


def _map_account_type(provider_type: ProviderAccountType) -> AccountType:
    """Map provider account type to account type."""
    mapping = {
        ProviderAccountType.CHECKING: AccountType.CHECKING,
        ProviderAccountType.SAVINGS: AccountType.SAVINGS,
        ProviderAccountType.CREDIT: AccountType.CHECKING,  # Map credit to checking for now
    }
    return mapping.get(provider_type, AccountType.CHECKING)


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
        reference_id: str,
        auth_code: str | None = None,
    ) -> BankConnectionWithAccountsResponse:
        """
        Complete OAuth flow and activate the bank connection.

        Fetches linked accounts from the provider and stores them.
        Creates an initial sync job.

        Args:
            user_id: User completing the OAuth flow
            reference_id: Reference ID from OAuth initiation (state parameter)
            auth_code: Authorization code from OAuth callback (required for EnableBanking)

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

        # For EnableBanking: exchange auth_code for session first
        if auth_code and hasattr(self.adapter, "complete_authorization"):
            # Find the connection matching this reference
            connection = None
            for conn in connections:
                if conn.provider_connection_id == reference_id:
                    connection = conn
                    break

            if not connection:
                # Check if there's already an active connection (duplicate callback)
                stmt_active = select(BankConnection).where(
                    BankConnection.user_id == user_id,
                    BankConnection.status == BankConnectionStatus.ACTIVE,
                ).order_by(BankConnection.updated_at.desc())
                result_active = await self.db.execute(stmt_active)
                active_conn = result_active.scalar_one_or_none()
                if active_conn:
                    # Return the existing active connection
                    return await self.get_connection(user_id, active_conn.id)  # type: ignore
                raise ValueError("No pending connection found for this reference")

            # Exchange code for session - this gives us the session_id and accounts
            try:
                requisition_status = await self.adapter.complete_authorization(auth_code)
                # Update connection with the new session_id
                connection.provider_connection_id = requisition_status.requisition_id
            except Exception as e:
                error_msg = str(e).lower()
                if "already authorized" in error_msg or "already used" in error_msg:
                    # Code was already exchanged - delete stale pending and ask to retry
                    await self.db.delete(connection)
                    await self.db.commit()
                    raise ValueError(
                        "This authorization link has expired. Please start a new connection."
                    ) from e
                raise
        else:
            # GoCardless flow: Find connection matching the requisition status
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
            # Create a regular Account for this bank account
            account_name = prov_acc.name or f"{connection.institution_name} Account"
            if prov_acc.account_number_masked:
                account_name = f"{account_name} ({prov_acc.account_number_masked})"

            account = Account(
                user_id=user_id,
                name=account_name,
                account_type=_map_account_type(prov_acc.account_type),
                balance=prov_acc.balance or 0,
                initial_balance=prov_acc.balance or 0,
                sync_status=SyncStatus.SUCCESS,
            )
            self.db.add(account)
            await self.db.flush()  # Get the account ID

            # Create LinkedAccount that references the Account
            linked_account = LinkedAccount(
                connection_id=connection.id,
                account_id=account.id,
                provider_account_id=prov_acc.id,
                account_name=prov_acc.name,
                account_number_masked=prov_acc.account_number_masked,
                account_type=_map_linked_account_type(prov_acc.account_type),
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
            List of BankConnectionResponse objects with computed health status
        """
        stmt = (
            select(BankConnection)
            .where(BankConnection.user_id == user_id)
            .order_by(BankConnection.created_at.desc())
        )
        result = await self.db.execute(stmt)
        connections = list(result.scalars().all())

        responses = []
        for conn in connections:
            response = BankConnectionResponse.model_validate(conn)
            response.health_status = self.compute_health_status(conn)
            responses.append(response)

        return responses

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

        health_status = self.compute_health_status(connection)

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
            health_status=health_status,
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

    # Health Monitoring Methods

    def compute_health_status(
        self,
        connection: BankConnection,
        warning_days: int = 7,
        stale_hours: int = 24,
    ) -> ConnectionHealthStatus:
        """
        Compute the health status of a bank connection.

        Args:
            connection: BankConnection model instance
            warning_days: Days before expiry to trigger warning (default 7)
            stale_hours: Hours since last sync to consider stale (default 24)

        Returns:
            ConnectionHealthStatus: HEALTHY, WARNING, or ERROR
        """
        now = datetime.now(UTC)

        # ERROR conditions
        if connection.status not in (
            BankConnectionStatus.ACTIVE,
            BankConnectionStatus.NEEDS_ATTENTION,
        ):
            return ConnectionHealthStatus.ERROR

        if (
            connection.access_valid_until is not None
            and connection.access_valid_until <= now
        ):
            return ConnectionHealthStatus.ERROR

        # WARNING conditions
        if connection.access_valid_until is not None:
            warning_threshold = now + timedelta(days=warning_days)
            if connection.access_valid_until <= warning_threshold:
                return ConnectionHealthStatus.WARNING

        # Check for stale sync (optional: only if last_sync_at is set)
        if connection.last_sync_at is not None:
            stale_threshold = now - timedelta(hours=stale_hours)
            if connection.last_sync_at < stale_threshold:
                # Check if last sync job failed
                # For now, treat as warning if sync is stale
                return ConnectionHealthStatus.WARNING

        return ConnectionHealthStatus.HEALTHY

    async def check_connection_health(
        self,
        connection_id: UUID,
    ) -> ConnectionHealthStatus | None:
        """
        Check the health status of a specific connection.

        Args:
            connection_id: Connection ID to check

        Returns:
            ConnectionHealthStatus if found, None if connection not found
        """
        stmt = select(BankConnection).where(BankConnection.id == connection_id)
        result = await self.db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            return None

        return self.compute_health_status(connection)

    async def detect_expiring_tokens(
        self,
        days_ahead: int = 7,
    ) -> list[BankConnection]:
        """
        Find connections with tokens expiring within the specified days.

        Used by scheduler to proactively notify users about expiring connections.

        Args:
            days_ahead: Number of days to look ahead (default 7)

        Returns:
            List of BankConnection objects needing re-authentication
        """
        now = datetime.now(UTC)
        threshold = now + timedelta(days=days_ahead)

        stmt = select(BankConnection).where(
            BankConnection.status == BankConnectionStatus.ACTIVE,
            BankConnection.access_valid_until.isnot(None),
            BankConnection.access_valid_until <= threshold,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def initiate_reauth(
        self,
        user_id: UUID,
        connection_id: UUID,
        redirect_url: str,
    ) -> OAuthInitResponse:
        """
        Initiate re-authentication for an existing connection.

        Similar to initiate_connection but for an existing connection
        that needs token refresh due to expiration.

        Args:
            user_id: User ID (for access control)
            connection_id: Connection ID to re-authenticate
            redirect_url: URL to redirect after OAuth

        Returns:
            OAuthInitResponse with authorization URL and reference ID

        Raises:
            ValueError: If connection not found or not owned by user
            RuntimeError: If requisition creation fails
        """
        # Find the existing connection
        stmt = select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            raise ValueError("Connection not found")

        # Validate connection can be re-authenticated
        if connection.status == BankConnectionStatus.DISCONNECTED:
            raise ValueError("Cannot re-authenticate a disconnected connection")

        # Get institution details from adapter
        institution = await self.adapter.get_institution(connection.institution_id)
        if not institution:
            raise ValueError(f"Institution no longer available: {connection.institution_id}")

        # Generate unique reference for tracking
        reference = str(uuid4())

        # Create new requisition with provider
        requisition = await self.adapter.create_requisition(
            institution_id=connection.institution_id,
            redirect_url=redirect_url,
            reference=reference,
        )

        # Update connection status and provider connection ID
        connection.status = BankConnectionStatus.PENDING_REAUTH
        connection.provider_connection_id = requisition.id
        connection.status_detail = "Re-authentication in progress"

        await self.db.commit()

        return OAuthInitResponse(
            authorization_url=requisition.link,
            reference_id=reference,
        )

    async def complete_reauth(
        self,
        user_id: UUID,
    ) -> BankConnectionWithAccountsResponse:
        """
        Complete re-authentication OAuth flow.

        Finds the pending re-auth connection and updates its access token.

        Args:
            user_id: User completing the OAuth flow

        Returns:
            BankConnectionWithAccountsResponse with updated connection

        Raises:
            ValueError: If no pending re-auth connection found
        """
        # Find the pending re-auth connection
        stmt = (
            select(BankConnection)
            .options(selectinload(BankConnection.linked_accounts))
            .where(
                BankConnection.user_id == user_id,
                BankConnection.status == BankConnectionStatus.PENDING_REAUTH,
            )
        )
        result = await self.db.execute(stmt)
        connections = list(result.scalars().all())

        # Find connection with completed requisition
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
            raise ValueError("No pending re-auth connection found or OAuth not completed")

        # Update connection with new access expiry
        connection.status = BankConnectionStatus.ACTIVE
        connection.status_detail = None
        connection.access_valid_until = requisition_status.access_valid_until

        await self.db.commit()
        await self.db.refresh(connection)

        health_status = self.compute_health_status(connection)

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
            health_status=health_status,
        )
