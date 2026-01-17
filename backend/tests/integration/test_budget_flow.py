"""
Integration tests for budget workflow.

Tests the complete budget lifecycle: categories, assignments, budget view.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.user import User


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_budget_workflow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test complete budget workflow: create categories, assign funds, view budget."""
    # Step 1: Create a user with an account
    user = User(
        email="budgetflow@example.com",
        password_hash=hash_password("BudgetTestPassword123!"),
        timezone="America/New_York",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("5000.00"),
        initial_balance=Decimal("5000.00"),
    )
    db_session.add(account)
    await db_session.flush()

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Step 2: Create a category group
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Monthly Bills", "display_order": 0},
    )
    assert group_response.status_code == 201
    group_data = group_response.json()
    group_id = group_data["id"]
    assert group_data["name"] == "Monthly Bills"

    # Step 3: Create a category
    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": "Rent"},
    )
    assert category_response.status_code == 201
    category_data = category_response.json()
    category_id = category_data["id"]
    assert category_data["name"] == "Rent"

    # Step 4: View initial budget (should show zero funded)
    budget_response = await client.get("/api/budget/2026-01")
    assert budget_response.status_code == 200
    budget_data = budget_response.json()
    assert budget_data["month"] == "2026-01"
    assert budget_data["to_assign"] == "5000.0000"  # Full balance unassigned

    # Find the category in the response
    rent_category = None
    for group in budget_data["groups"]:
        for cat in group["categories"]:
            if cat["id"] == category_id:
                rent_category = cat
                break

    assert rent_category is not None
    assert rent_category["funded_this_month"] == "0"
    assert rent_category["activity"] == "0"
    assert rent_category["available"] == "0"

    # Step 5: Assign funds to the category
    assign_response = await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "1500.00", "month": "2026-01-01"},
    )
    assert assign_response.status_code == 201
    assign_data = assign_response.json()
    assert assign_data["amount"] == "1500.00"

    # Step 6: View budget again - should show updated values
    budget_response2 = await client.get("/api/budget/2026-01")
    assert budget_response2.status_code == 200
    budget_data2 = budget_response2.json()

    # To assign should decrease by the amount we assigned
    assert budget_data2["to_assign"] == "3500.0000"

    # Find the category again
    rent_category2 = None
    for group in budget_data2["groups"]:
        for cat in group["categories"]:
            if cat["id"] == category_id:
                rent_category2 = cat
                break

    assert rent_category2 is not None
    assert rent_category2["funded_this_month"] == "1500.0000"
    assert rent_category2["available"] == "1500.0000"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_budget_rollover_across_months(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that unused funds roll over to the next month."""
    # Create a user with an account
    user = User(
        email="rolloverflow@example.com",
        password_hash=hash_password("RolloverTestPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("3000.00"),
        initial_balance=Decimal("3000.00"),
    )
    db_session.add(account)
    await db_session.flush()

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create a category group and category
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Savings Goals", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": "Vacation"},
    )
    category_id = category_response.json()["id"]

    # Assign funds in January
    await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "500.00", "month": "2026-01-01"},
    )

    # View January budget - should show 500 available
    jan_budget = await client.get("/api/budget/2026-01")
    jan_data = jan_budget.json()

    jan_category = None
    for group in jan_data["groups"]:
        for cat in group["categories"]:
            if cat["id"] == category_id:
                jan_category = cat
                break

    assert jan_category["funded_this_month"] == "500.0000"
    assert jan_category["available"] == "500.0000"

    # View February budget - January funds should roll over
    feb_budget = await client.get("/api/budget/2026-02")
    feb_data = feb_budget.json()

    feb_category = None
    for group in feb_data["groups"]:
        for cat in group["categories"]:
            if cat["id"] == category_id:
                feb_category = cat
                break

    # February shows 0 funded this month, but 500 available from rollover
    assert feb_category["funded_this_month"] == "0"
    assert feb_category["available"] == "500.0000"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_categories_and_assignments(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test budget workflow with multiple categories."""
    # Create a user with an account
    user = User(
        email="multicat@example.com",
        password_hash=hash_password("MultiCatPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    account = Account(
        user_id=user.id,
        name="Checking",
        account_type=AccountType.CHECKING,
        balance=Decimal("2000.00"),
        initial_balance=Decimal("2000.00"),
    )
    db_session.add(account)
    await db_session.flush()

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create category groups
    bills_response = await client.post(
        "/api/categories/groups",
        json={"name": "Bills", "display_order": 0},
    )
    bills_group_id = bills_response.json()["id"]

    savings_response = await client.post(
        "/api/categories/groups",
        json={"name": "Savings", "display_order": 1},
    )
    savings_group_id = savings_response.json()["id"]

    # Create categories
    rent_response = await client.post(
        "/api/categories/",
        json={"group_id": bills_group_id, "name": "Rent"},
    )
    rent_id = rent_response.json()["id"]

    utilities_response = await client.post(
        "/api/categories/",
        json={"group_id": bills_group_id, "name": "Utilities"},
    )
    utilities_id = utilities_response.json()["id"]

    emergency_response = await client.post(
        "/api/categories/",
        json={"group_id": savings_group_id, "name": "Emergency Fund"},
    )
    emergency_id = emergency_response.json()["id"]

    # Assign funds to each category
    await client.post(
        f"/api/categories/{rent_id}/assign",
        json={"amount": "1000.00", "month": "2026-01-01"},
    )
    await client.post(
        f"/api/categories/{utilities_id}/assign",
        json={"amount": "200.00", "month": "2026-01-01"},
    )
    await client.post(
        f"/api/categories/{emergency_id}/assign",
        json={"amount": "300.00", "month": "2026-01-01"},
    )

    # View budget
    budget_response = await client.get("/api/budget/2026-01")
    budget_data = budget_response.json()

    # Verify to_assign: 2000 - 1000 - 200 - 300 = 500
    assert budget_data["to_assign"] == "500.0000"

    # Verify we have 2 groups
    assert len(budget_data["groups"]) == 2

    # Check categories
    categories_by_id = {}
    for group in budget_data["groups"]:
        for cat in group["categories"]:
            categories_by_id[cat["id"]] = cat

    assert categories_by_id[rent_id]["funded_this_month"] == "1000.0000"
    assert categories_by_id[utilities_id]["funded_this_month"] == "200.0000"
    assert categories_by_id[emergency_id]["funded_this_month"] == "300.0000"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unassign_funds(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test unassigning funds from a category."""
    # Create a user with an account
    user = User(
        email="unassignflow@example.com",
        password_hash=hash_password("UnassignTestPassword123!"),
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

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Create a category group and category
    group_response = await client.post(
        "/api/categories/groups",
        json={"name": "Discretionary", "display_order": 0},
    )
    group_id = group_response.json()["id"]

    category_response = await client.post(
        "/api/categories/",
        json={"group_id": group_id, "name": "Entertainment"},
    )
    category_id = category_response.json()["id"]

    # Assign 500
    await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "500.00", "month": "2026-01-01"},
    )

    # Check budget - to_assign should be 500
    budget1 = await client.get("/api/budget/2026-01")
    assert budget1.json()["to_assign"] == "500.0000"

    # Unassign 200 (negative amount)
    unassign_response = await client.post(
        f"/api/categories/{category_id}/assign",
        json={"amount": "-200.00", "month": "2026-01-01"},
    )
    assert unassign_response.status_code == 201
    assert unassign_response.json()["amount"] == "-200.00"

    # Check budget again - to_assign should be 700 (1000 - 500 + 200)
    budget2 = await client.get("/api/budget/2026-01")
    assert budget2.json()["to_assign"] == "700.0000"

    # Category should show 300 available (500 - 200)
    category_budget = None
    for group in budget2.json()["groups"]:
        for cat in group["categories"]:
            if cat["id"] == category_id:
                category_budget = cat
                break

    assert category_budget["funded_this_month"] == "300.0000"
    assert category_budget["available"] == "300.0000"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fund_underfunded_workflow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test complete funding workflow: set targets, get underfunded, auto-fund (T148)."""
    # Step 1: Create a user with an account
    user = User(
        email="fundingflow@example.com",
        password_hash=hash_password("FundingTestPassword123!"),
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

    # Login
    token = create_session_token(user.id)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    # Step 2: Create category groups with different priorities
    bills_response = await client.post(
        "/api/categories/groups",
        json={"name": "Bills", "display_order": 0},  # Priority 0 (first)
    )
    assert bills_response.status_code == 201
    bills_group_id = bills_response.json()["id"]

    savings_response = await client.post(
        "/api/categories/groups",
        json={"name": "Savings", "display_order": 1},  # Priority 1 (second)
    )
    assert savings_response.status_code == 201
    savings_group_id = savings_response.json()["id"]

    # Step 3: Create categories
    rent_response = await client.post(
        "/api/categories/",
        json={"group_id": bills_group_id, "name": "Rent"},
    )
    rent_id = rent_response.json()["id"]

    utilities_response = await client.post(
        "/api/categories/",
        json={"group_id": bills_group_id, "name": "Utilities"},
    )
    utilities_id = utilities_response.json()["id"]

    emergency_response = await client.post(
        "/api/categories/",
        json={"group_id": savings_group_id, "name": "Emergency"},
    )
    emergency_id = emergency_response.json()["id"]

    # Step 4: Set targets for each category
    rent_target_response = await client.post(
        "/api/targets/",
        json={
            "category_id": rent_id,
            "target_type": "MONTHLY_NEEDED",
            "amount": "500.00",
        },
    )
    assert rent_target_response.status_code == 201

    utilities_target_response = await client.post(
        "/api/targets/",
        json={
            "category_id": utilities_id,
            "target_type": "MONTHLY_NEEDED",
            "amount": "200.00",
        },
    )
    assert utilities_target_response.status_code == 201

    emergency_target_response = await client.post(
        "/api/targets/",
        json={
            "category_id": emergency_id,
            "target_type": "TARGET_BALANCE",
            "amount": "1000.00",  # Want to save $1000 total
        },
    )
    assert emergency_target_response.status_code == 201

    # Step 5: Get underfunded summary
    summary_response = await client.get("/api/budget/2026-01/underfunded-summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()

    # Total underfunded: 500 + 200 + 1000 = 1700
    assert Decimal(summary["total_underfunded"]) == Decimal("1700.00")
    assert len(summary["categories"]) == 3

    # Step 6: Fund single category (utilities)
    fund_single_response = await client.post(
        f"/api/budget/2026-01/fund-underfunded/{utilities_id}"
    )
    assert fund_single_response.status_code == 200
    fund_single_data = fund_single_response.json()

    assert Decimal(fund_single_data["amount_funded"]) == Decimal("200.00")
    assert fund_single_data["is_partial"] is False

    # Check budget - to_assign should decrease
    budget1 = await client.get("/api/budget/2026-01")
    assert Decimal(budget1.json()["to_assign"]) == Decimal("800.00")

    # Step 7: Fund all remaining underfunded
    # Remaining: Rent (500) + Emergency (1000) = 1500, but only 800 to assign
    fund_all_response = await client.post("/api/budget/2026-01/fund-all-underfunded")
    assert fund_all_response.status_code == 200
    fund_all_data = fund_all_response.json()

    # Should fund partially (800 available)
    assert Decimal(fund_all_data["total_funded"]) == Decimal("800.00")
    assert Decimal(fund_all_data["total_underfunded"]) == Decimal("1500.00")
    assert fund_all_data["is_partial"] is True
    # Rent (priority 0) gets 500, Emergency (priority 1) gets remaining 300
    assert fund_all_data["categories_funded"] == 2

    # Step 8: Verify final budget state
    final_budget = await client.get("/api/budget/2026-01")
    final_data = final_budget.json()

    # All funds assigned (started with 1000, assigned 200 + 800 = 1000)
    assert Decimal(final_data["to_assign"]) == Decimal("0.00")

    # Check each category
    categories_by_id = {}
    for group in final_data["groups"]:
        for cat in group["categories"]:
            categories_by_id[cat["id"]] = cat

    # Rent: fully funded (500)
    assert Decimal(categories_by_id[rent_id]["funded_this_month"]) == Decimal("500.00")

    # Utilities: funded earlier (200)
    assert Decimal(categories_by_id[utilities_id]["funded_this_month"]) == Decimal("200.00")

    # Emergency: partially funded (300 out of 1000)
    assert Decimal(categories_by_id[emergency_id]["funded_this_month"]) == Decimal("300.00")
