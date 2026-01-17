"""
Integration tests for month navigation with targets.

Tests how all three target types behave when navigating between months.
Covers User Story 6 - Month Rollover.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.user import User


async def setup_user_with_account(
    db_session: AsyncSession, email: str, balance: str = "2000.00"
) -> tuple:
    """Helper to create user with account."""
    user = User(
        email=email,
        password_hash=hash_password("TestPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal(balance),
        initial_balance=Decimal(balance),
    )
    db_session.add(account)
    await db_session.flush()

    return user, account


async def setup_category_with_target(
    client: AsyncClient,
    group_id: str,
    name: str,
    target_type: str,
    amount: str,
    target_date: str | None = None,
) -> tuple:
    """Helper to create category and target."""
    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": name},
    )
    category_id = category_response.json()["id"]

    target_data = {
        "category_id": category_id,
        "target_type": target_type,
        "amount": amount,
    }
    if target_date:
        target_data["target_date"] = target_date

    target_response = await client.post("/api/targets/", json=target_data)
    target_id = target_response.json()["id"]

    return category_id, target_id


def get_category_from_budget(budget_data: dict, category_id: str) -> dict | None:
    """Helper to find category in budget response."""
    for group in budget_data["groups"]:
        for cat in group["categories"]:
            if cat["id"] == category_id:
                return cat
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_monthly_needed_resets_each_month(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that MONTHLY_NEEDED targets show underfunded each month (T157).

    Scenario:
    - Set up a $200/month target
    - Fully fund in January
    - Navigate to February -> should show $200 underfunded again
    """
    user, _ = await setup_user_with_account(
        db_session, "monthly_reset@example.com", "1000.00"
    )

    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category group and category with MONTHLY_NEEDED target
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Bills", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_id, _ = await setup_category_with_target(
        client, group_id, "Rent", "MONTHLY_NEEDED", "200.00"
    )

    # January: Check underfunded (should be $200)
    jan_summary = await client.get("/api/budget/2026-01/underfunded-summary")
    jan_summary_data = jan_summary.json()
    assert Decimal(jan_summary_data["total_underfunded"]) == Decimal("200.00")

    # Fund the target in January
    await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "200.00", "month": "2026-01-01"},
    )

    # January: Verify fully funded
    jan_funded_summary = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_funded_summary.json()["total_underfunded"]) == Decimal("0.00")

    # February: Should reset - $200 underfunded again
    feb_summary = await client.get("/api/budget/2026-02/underfunded-summary")
    feb_summary_data = feb_summary.json()
    assert Decimal(feb_summary_data["total_underfunded"]) == Decimal("200.00")

    # February budget view: funded_this_month should be 0
    feb_budget = await client.get("/api/budget/2026-02")
    feb_category = get_category_from_budget(feb_budget.json(), category_id)
    assert Decimal(feb_category["funded_this_month"]) == Decimal("0")
    # Available should be 200 (rolled over from January)
    assert Decimal(feb_category["available"]) == Decimal("200.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_target_balance_persists_across_months(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that TARGET_BALANCE uses available balance across months (T158).

    Scenario:
    - Set up a $1000 balance target
    - Fund $400 in January
    - Navigate to February -> should show $600 underfunded (balance persists)
    - Fund $300 more in February -> should show $300 underfunded
    """
    user, _ = await setup_user_with_account(
        db_session, "balance_persist@example.com", "2000.00"
    )

    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category with TARGET_BALANCE
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Savings", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_id, _ = await setup_category_with_target(
        client, group_id, "Emergency Fund", "TARGET_BALANCE", "1000.00"
    )

    # January: Initial underfunded = $1000
    jan_summary = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_summary.json()["total_underfunded"]) == Decimal("1000.00")

    # Fund $400 in January
    await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "400.00", "month": "2026-01-01"},
    )

    # January: Now $600 underfunded
    jan_after = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_after.json()["total_underfunded"]) == Decimal("600.00")

    # February: Still $600 underfunded (balance carries over)
    feb_summary = await client.get("/api/budget/2026-02/underfunded-summary")
    assert Decimal(feb_summary.json()["total_underfunded"]) == Decimal("600.00")

    # February budget view: funded_this_month=0, available=$400
    feb_budget = await client.get("/api/budget/2026-02")
    feb_category = get_category_from_budget(feb_budget.json(), category_id)
    assert Decimal(feb_category["funded_this_month"]) == Decimal("0")
    assert Decimal(feb_category["available"]) == Decimal("400.00")

    # Fund $300 more in February
    await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "300.00", "month": "2026-02-01"},
    )

    # February: Now $300 underfunded
    feb_after = await client.get("/api/budget/2026-02/underfunded-summary")
    assert Decimal(feb_after.json()["total_underfunded"]) == Decimal("300.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_target_by_date_suggested_monthly_increases(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that TARGET_BY_DATE increases suggested amount as deadline approaches (T159).

    Scenario:
    - Set up a $600 target by June 2026 (6 months)
    - January: suggested = $100/month (600/6)
    - February: suggested = $120/month (600/5) if not funded
    - Fund in January, February should adjust based on available
    """
    user, _ = await setup_user_with_account(
        db_session, "date_target@example.com", "1500.00"
    )

    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category with TARGET_BY_DATE
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Goals", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_id, target_id = await setup_category_with_target(
        client,
        group_id,
        "Vacation",
        "TARGET_BY_DATE",
        "600.00",
        target_date="2026-06-01",
    )

    # January: 6 months, suggested = 600/6 = $100
    jan_summary = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_summary.json()["total_underfunded"]) == Decimal("100.00")

    # Get target details for January
    jan_target = await client.get(f"/api/targets/{target_id}/underfunded?month=2026-01-01")
    jan_target_data = jan_target.json()
    assert Decimal(jan_target_data["underfunded"]) == Decimal("100.00")
    assert Decimal(jan_target_data["suggested_monthly"]) == Decimal("100.00")

    # Fund $100 in January
    await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "100.00", "month": "2026-01-01"},
    )

    # January: Now fully funded for this month
    jan_after = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_after.json()["total_underfunded"]) == Decimal("0.00")

    # February: 5 months, needed = 600 - 100 = 500
    # suggested = 500/5 = $100 (same since we kept pace)
    feb_summary = await client.get("/api/budget/2026-02/underfunded-summary")
    assert Decimal(feb_summary.json()["total_underfunded"]) == Decimal("100.00")

    # Get target details for February
    feb_target = await client.get(f"/api/targets/{target_id}/underfunded?month=2026-02-01")
    feb_target_data = feb_target.json()
    assert Decimal(feb_target_data["suggested_monthly"]) == Decimal("100.00")

    # Skip funding in February, check March
    # March: 4 months, needed = 500 (nothing added in Feb)
    # suggested = 500/4 = $125
    mar_target = await client.get(f"/api/targets/{target_id}/underfunded?month=2026-03-01")
    mar_target_data = mar_target.json()
    assert Decimal(mar_target_data["suggested_monthly"]) == Decimal("125.00")
    assert Decimal(mar_target_data["underfunded"]) == Decimal("125.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_target_types_month_navigation(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test navigating between months with all three target types.

    Combined scenario:
    - MONTHLY_NEEDED: $200/month
    - TARGET_BALANCE: $500 total
    - TARGET_BY_DATE: $300 by March (3 months from Jan)
    """
    user, _ = await setup_user_with_account(
        db_session, "all_targets@example.com", "2000.00"
    )

    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create categories with different target types
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Budget", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    monthly_id, _ = await setup_category_with_target(
        client, group_id, "Monthly Bill", "MONTHLY_NEEDED", "200.00"
    )

    balance_id, _ = await setup_category_with_target(
        client, group_id, "Savings Goal", "TARGET_BALANCE", "500.00"
    )

    date_id, _ = await setup_category_with_target(
        client, group_id, "Trip Fund", "TARGET_BY_DATE", "300.00", "2026-03-01"
    )

    # January underfunded:
    # - Monthly: $200
    # - Balance: $500
    # - Date: 300/3 = $100
    # Total: $800
    jan_summary = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_summary.json()["total_underfunded"]) == Decimal("800.00")

    # Fund everything in January
    await client.post(
        f"/api/categories/{monthly_id}/assign",
        json={"amount": "200.00", "month": "2026-01-01"},
    )
    await client.post(
        f"/api/categories/{balance_id}/assign",
        json={"amount": "200.00", "month": "2026-01-01"},  # Partial toward $500
    )
    await client.post(
        f"/api/categories/{date_id}/assign",
        json={"amount": "100.00", "month": "2026-01-01"},
    )

    # January after funding:
    # - Monthly: $0 (fully funded)
    # - Balance: $300 (500 - 200)
    # - Date: $0 (funded suggested)
    # Total: $300
    jan_after = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_after.json()["total_underfunded"]) == Decimal("300.00")

    # Navigate to February:
    # - Monthly: $200 (resets!)
    # - Balance: $300 (still needs $300)
    # - Date: 2 months left, needed = 200, suggested = $100
    # Total: $600
    feb_summary = await client.get("/api/budget/2026-02/underfunded-summary")
    assert Decimal(feb_summary.json()["total_underfunded"]) == Decimal("600.00")

    # Verify February budget view
    feb_budget = await client.get("/api/budget/2026-02")
    feb_data = feb_budget.json()

    monthly_cat = get_category_from_budget(feb_data, monthly_id)
    balance_cat = get_category_from_budget(feb_data, balance_id)
    date_cat = get_category_from_budget(feb_data, date_id)

    # Monthly: funded_this_month=0, available=200 (rolled over)
    assert Decimal(monthly_cat["funded_this_month"]) == Decimal("0")
    assert Decimal(monthly_cat["available"]) == Decimal("200.00")

    # Balance: funded_this_month=0, available=200 (rolled over)
    assert Decimal(balance_cat["funded_this_month"]) == Decimal("0")
    assert Decimal(balance_cat["available"]) == Decimal("200.00")

    # Date: funded_this_month=0, available=100 (rolled over)
    assert Decimal(date_cat["funded_this_month"]) == Decimal("0")
    assert Decimal(date_cat["available"]) == Decimal("100.00")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auto_fund_respects_month_context(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that auto-funding uses correct month context for calculations."""
    user, _ = await setup_user_with_account(
        db_session, "auto_fund_month@example.com", "1000.00"
    )

    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category with MONTHLY_NEEDED target
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Bills", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_id, _ = await setup_category_with_target(
        client, group_id, "Utilities", "MONTHLY_NEEDED", "150.00"
    )

    # Auto-fund for January
    jan_fund = await client.post("/api/budget/2026-01/fund-all-underfunded")
    assert Decimal(jan_fund.json()["total_funded"]) == Decimal("150.00")

    # January should be fully funded
    jan_summary = await client.get("/api/budget/2026-01/underfunded-summary")
    assert Decimal(jan_summary.json()["total_underfunded"]) == Decimal("0.00")

    # Auto-fund for February (should fund $150 again)
    feb_fund = await client.post("/api/budget/2026-02/fund-all-underfunded")
    assert Decimal(feb_fund.json()["total_funded"]) == Decimal("150.00")

    # Both months should show as funded
    jan_check = await client.get("/api/budget/2026-01/underfunded-summary")
    feb_check = await client.get("/api/budget/2026-02/underfunded-summary")

    assert Decimal(jan_check.json()["total_underfunded"]) == Decimal("0.00")
    assert Decimal(feb_check.json()["total_underfunded"]) == Decimal("0.00")
