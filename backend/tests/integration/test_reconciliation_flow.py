"""
Integration tests for reconciliation workflow.

Tests the complete reconciliation lifecycle: start, mark cleared, adjust, complete.
"""
from decimal import Decimal
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import create_session_token, SESSION_COOKIE_NAME
from mybudget.models.user import User
from mybudget.models.account import Account, AccountType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_reconciliation_workflow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test complete reconciliation workflow: start, mark cleared, complete."""
    # Step 1: Create a user with an account
    user = User(
        email="reconflow@example.com",
        password_hash=hash_password("ReconTestPassword123!"),
        timezone="America/New_York",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("1000.00"),
        initial_balance=Decimal("1000.00"),
    )
    db_session.add(account)
    await db_session.flush()
    account_id = str(account.id)

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Step 2: Create a category group and category for transactions
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Monthly Bills", "display_order": 0},
    )
    assert group_response.status_code == 201
    group_id = group_response.json()["id"]

    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": "Groceries"},
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    # Step 3: Create and approve some transactions
    transactions = []
    for i, amount in enumerate(["-100.00", "-50.00", "-25.00"]):
        tx_response = await client.post(
            "/api/transactions/",
            json={
                "account_id": account_id,
                "amount": amount,
                "date": (date.today() - timedelta(days=i)).isoformat(),
                "payee": f"Store {i}",
                "memo": f"Purchase {i}",
            },
        )
        assert tx_response.status_code == 201
        tx = tx_response.json()

        # Approve the transaction with a category
        approve_response = await client.post(
            f"/api/transactions/{tx['id']}/approve",
            json={"category_id": category_id},
        )
        assert approve_response.status_code == 200
        transactions.append(approve_response.json())

    # Step 4: Start reconciliation
    # Account balance should be: 1000 - 100 - 50 - 25 = 825
    recon_response = await client.post(
        "/api/reconciliations/",
        json={
            "account_id": account_id,
            "statement_balance": "825.00",
            "statement_date": date.today().isoformat(),
        },
    )
    assert recon_response.status_code == 201
    recon_data = recon_response.json()
    recon_id = recon_data["id"]

    assert recon_data["status"] == "IN_PROGRESS"
    assert "cleared_balance" in recon_data
    assert "discrepancy" in recon_data

    # Step 5: Mark all transactions as cleared
    mark_response = await client.put(
        f"/api/reconciliations/{recon_id}/mark-cleared",
        json={"transaction_ids": [tx["id"] for tx in transactions]},
    )
    assert mark_response.status_code == 200
    mark_data = mark_response.json()

    # After marking all as cleared, discrepancy should be 0
    # Cleared balance: 1000 (starting) - 175 (transactions) = 825
    assert "cleared_balance" in mark_data

    # Step 6: Complete the reconciliation
    complete_response = await client.post(f"/api/reconciliations/{recon_id}/complete")
    assert complete_response.status_code == 200
    complete_data = complete_response.json()

    assert complete_data["status"] == "COMPLETED"
    assert complete_data["completed_at"] is not None

    # Step 7: Verify transactions are now locked (cleared during reconciliation)
    # Get one of the cleared transactions
    tx_response = await client.get(f"/api/transactions/{transactions[0]['id']}")
    assert tx_response.status_code == 200
    tx_data = tx_response.json()
    assert tx_data["state"] == "CLEARED"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reconciliation_with_adjustment(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test reconciliation with discrepancy requiring adjustment transaction."""
    # Step 1: Create a user with an account
    user = User(
        email="reconadjust@example.com",
        password_hash=hash_password("ReconAdjustPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Savings",
        account_type=AccountType.SAVINGS,
        balance=Decimal("500.00"),
        initial_balance=Decimal("500.00"),
    )
    db_session.add(account)
    await db_session.flush()
    account_id = str(account.id)

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category for adjustment
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Adjustments", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": "Reconciliation Adjustments"},
    )
    adjustment_category_id = category_response.json()["id"]

    # Step 2: Start reconciliation with a discrepancy
    # No transactions, but statement says 490 (10 less than actual)
    recon_response = await client.post(
        "/api/reconciliations/",
        json={
            "account_id": account_id,
            "statement_balance": "490.00",  # Discrepancy of -10
            "statement_date": date.today().isoformat(),
        },
    )
    assert recon_response.status_code == 201
    recon_id = recon_response.json()["id"]

    # Step 3: Create adjustment to fix discrepancy
    adjust_response = await client.post(
        f"/api/reconciliations/{recon_id}/create-adjustment",
        json={"category_id": adjustment_category_id},
    )
    assert adjust_response.status_code == 201
    adjust_data = adjust_response.json()

    assert "adjustment_transaction" in adjust_data
    adjustment_tx = adjust_data["adjustment_transaction"]
    # Adjustment should be -10.00 to bring 500 down to 490
    assert Decimal(adjustment_tx["amount"]) == Decimal("-10.00")

    # Step 4: Complete the reconciliation
    complete_response = await client.post(f"/api/reconciliations/{recon_id}/complete")
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"

    # Verify adjustment transaction exists
    adjustment_tx_response = await client.get(
        f"/api/transactions/{adjustment_tx['id']}"
    )
    assert adjustment_tx_response.status_code == 200
    assert adjustment_tx_response.json()["memo"] == "Reconciliation Adjustment"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cancel_reconciliation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test canceling an in-progress reconciliation."""
    # Create a user with an account
    user = User(
        email="reconcancel@example.com",
        password_hash=hash_password("ReconCancelPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("1000.00"),
        initial_balance=Decimal("1000.00"),
    )
    db_session.add(account)
    await db_session.flush()
    account_id = str(account.id)

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Start reconciliation
    recon_response = await client.post(
        "/api/reconciliations/",
        json={
            "account_id": account_id,
            "statement_balance": "1000.00",
            "statement_date": date.today().isoformat(),
        },
    )
    assert recon_response.status_code == 201
    recon_id = recon_response.json()["id"]

    # Cancel the reconciliation
    cancel_response = await client.delete(f"/api/reconciliations/{recon_id}")
    assert cancel_response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/reconciliations/{recon_id}")
    assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reconciliation_prevents_transaction_modification(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that cleared transactions cannot be modified after reconciliation."""
    # Create a user with an account
    user = User(
        email="reconlock@example.com",
        password_hash=hash_password("ReconLockPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("500.00"),
        initial_balance=Decimal("500.00"),
    )
    db_session.add(account)
    await db_session.flush()
    account_id = str(account.id)

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Bills", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": "Utilities"},
    )
    category_id = category_response.json()["id"]

    # Create and approve a transaction
    tx_response = await client.post(
        "/api/transactions/",
        json={
            "account_id": account_id,
            "amount": "-50.00",
            "date": date.today().isoformat(),
            "payee": "Electric Company",
        },
    )
    tx = tx_response.json()

    approve_response = await client.post(
        f"/api/transactions/{tx['id']}/approve",
        json={"category_id": category_id},
    )
    assert approve_response.status_code == 200
    tx_id = tx["id"]

    # Start reconciliation
    recon_response = await client.post(
        "/api/reconciliations/",
        json={
            "account_id": account_id,
            "statement_balance": "450.00",  # 500 - 50
            "statement_date": date.today().isoformat(),
        },
    )
    recon_id = recon_response.json()["id"]

    # Mark transaction as cleared
    await client.put(
        f"/api/reconciliations/{recon_id}/mark-cleared",
        json={"transaction_ids": [tx_id]},
    )

    # Complete reconciliation
    await client.post(f"/api/reconciliations/{recon_id}/complete")

    # Try to modify the cleared transaction - should fail
    modify_response = await client.put(
        f"/api/transactions/{tx_id}",
        json={"amount": "-100.00"},
    )
    # Cleared transactions should not be modifiable
    assert modify_response.status_code in [400, 403]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_reconciliations_for_account(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that an account can have multiple completed reconciliations."""
    # Create a user with an account
    user = User(
        email="reconmulti@example.com",
        password_hash=hash_password("ReconMultiPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("1000.00"),
        initial_balance=Decimal("1000.00"),
    )
    db_session.add(account)
    await db_session.flush()
    account_id = str(account.id)

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # First reconciliation
    recon1_response = await client.post(
        "/api/reconciliations/",
        json={
            "account_id": account_id,
            "statement_balance": "1000.00",
            "statement_date": (date.today() - timedelta(days=30)).isoformat(),
        },
    )
    assert recon1_response.status_code == 201
    recon1_id = recon1_response.json()["id"]

    await client.post(f"/api/reconciliations/{recon1_id}/complete")

    # Second reconciliation (later date)
    recon2_response = await client.post(
        "/api/reconciliations/",
        json={
            "account_id": account_id,
            "statement_balance": "1000.00",
            "statement_date": date.today().isoformat(),
        },
    )
    assert recon2_response.status_code == 201
    recon2_id = recon2_response.json()["id"]

    await client.post(f"/api/reconciliations/{recon2_id}/complete")

    # List reconciliations for account
    list_response = await client.get(
        f"/api/reconciliations/", params={"account_id": account_id}
    )
    assert list_response.status_code == 200
    reconciliations = list_response.json()

    assert len(reconciliations) == 2
    assert all(r["status"] == "COMPLETED" for r in reconciliations)
