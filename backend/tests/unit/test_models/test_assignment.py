"""
Unit tests for Assignment model.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from mybudget.models.assignment import Assignment


class TestAssignmentModel:
    """Unit tests for Assignment model."""

    def test_create_assignment(self) -> None:
        """Test creating an assignment with valid data."""
        user_id = uuid4()
        category_id = uuid4()

        assignment = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("500.00"),
            month=date(2026, 1, 1),
        )

        assert assignment.user_id == user_id
        assert assignment.category_id == category_id
        assert assignment.amount == Decimal("500.00")
        assert assignment.month == date(2026, 1, 1)

    def test_assignment_positive_amount(self) -> None:
        """Test assignment with positive amount (assigning funds)."""
        assignment = Assignment(
            user_id=uuid4(),
            category_id=uuid4(),
            amount=Decimal("100.00"),
            month=date(2026, 1, 1),
        )

        assert assignment.amount > 0

    def test_assignment_negative_amount(self) -> None:
        """Test assignment with negative amount (unassigning funds)."""
        assignment = Assignment(
            user_id=uuid4(),
            category_id=uuid4(),
            amount=Decimal("-50.00"),
            month=date(2026, 1, 1),
        )

        assert assignment.amount < 0

    def test_assignment_decimal_precision(self) -> None:
        """Test assignment maintains decimal precision."""
        assignment = Assignment(
            user_id=uuid4(),
            category_id=uuid4(),
            amount=Decimal("123.4567"),
            month=date(2026, 1, 1),
        )

        assert assignment.amount == Decimal("123.4567")

    def test_assignment_month_is_first_day(self) -> None:
        """Test that month should be first day of month."""
        # This is a business rule enforced by validation, not the model itself
        # The model accepts any date, but validation should ensure first-of-month
        assignment = Assignment(
            user_id=uuid4(),
            category_id=uuid4(),
            amount=Decimal("100.00"),
            month=date(2026, 1, 1),
        )

        assert assignment.month.day == 1

    def test_assignment_repr(self) -> None:
        """Test assignment string representation."""
        assignment = Assignment(
            user_id=uuid4(),
            category_id=uuid4(),
            amount=Decimal("100.00"),
            month=date(2026, 1, 1),
        )

        repr_str = repr(assignment)
        assert "Assignment" in repr_str
        assert "100" in repr_str
        assert "2026-01-01" in repr_str


class TestAssignmentBusinessRules:
    """Test business rules for assignments."""

    def test_multiple_assignments_same_category_month(self) -> None:
        """Test that multiple assignments can exist for same category/month."""
        user_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        # Append-only: multiple assignments are valid
        a1 = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("100.00"),
            month=month,
        )
        a2 = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("50.00"),
            month=month,
        )

        # Total funded = sum of all assignments
        total = a1.amount + a2.amount
        assert total == Decimal("150.00")

    def test_unassign_creates_negative_assignment(self) -> None:
        """Test that unassigning creates a negative assignment record."""
        user_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        # Assign 100
        assign = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("100.00"),
            month=month,
        )

        # Unassign 30
        unassign = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("-30.00"),
            month=month,
        )

        # Net funded = 100 - 30 = 70
        net_funded = assign.amount + unassign.amount
        assert net_funded == Decimal("70.00")

    def test_assignment_different_months_independent(self) -> None:
        """Test that assignments for different months are independent."""
        user_id = uuid4()
        category_id = uuid4()

        jan_assign = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("100.00"),
            month=date(2026, 1, 1),
        )

        feb_assign = Assignment(
            user_id=user_id,
            category_id=category_id,
            amount=Decimal("200.00"),
            month=date(2026, 2, 1),
        )

        # Each month has its own assignment amount
        assert jan_assign.amount == Decimal("100.00")
        assert feb_assign.amount == Decimal("200.00")
        assert jan_assign.month != feb_assign.month
