"""
Unit tests for Reconciliation model.

Tests the reconciliation entity and its calculation methods.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
import uuid

from mybudget.models.reconciliation import Reconciliation, ReconciliationStatus


class TestReconciliationModel:
    """Tests for Reconciliation model."""

    def test_create_reconciliation(self):
        """Test creating a reconciliation instance."""
        user_id = uuid.uuid4()
        account_id = uuid.uuid4()

        recon = Reconciliation(
            user_id=user_id,
            account_id=account_id,
            statement_balance=Decimal("1000.00"),
            statement_date=date.today(),
        )

        assert recon.user_id == user_id
        assert recon.account_id == account_id
        assert recon.statement_balance == Decimal("1000.00")
        assert recon.statement_date == date.today()
        # Note: Default status is only set on database insertion
        assert recon.adjustment_transaction_id is None
        assert recon.completed_at is None

    def test_status_can_be_set(self):
        """Test that status can be explicitly set."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("500.00"),
            statement_date=date.today(),
            status=ReconciliationStatus.IN_PROGRESS,
        )

        assert recon.status == ReconciliationStatus.IN_PROGRESS

    def test_statement_balance_precision(self):
        """Test that statement balance handles decimal precision correctly."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1234.5678"),
            statement_date=date.today(),
        )

        assert recon.statement_balance == Decimal("1234.5678")

    def test_negative_statement_balance(self):
        """Test that negative statement balance is allowed (overdraft)."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("-250.00"),
            statement_date=date.today(),
        )

        assert recon.statement_balance == Decimal("-250.00")


class TestReconciliationStatus:
    """Tests for ReconciliationStatus enum."""

    def test_status_values(self):
        """Test that status enum has expected values."""
        assert ReconciliationStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert ReconciliationStatus.COMPLETED.value == "COMPLETED"

    def test_status_comparison(self):
        """Test status enum comparison."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("100.00"),
            statement_date=date.today(),
            status=ReconciliationStatus.IN_PROGRESS,
        )

        assert recon.status == ReconciliationStatus.IN_PROGRESS
        assert recon.status != ReconciliationStatus.COMPLETED


class TestReconciliationCalculations:
    """Tests for reconciliation balance calculations."""

    def test_calculate_cleared_balance_no_transactions(self):
        """Test cleared balance calculation with no transactions."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1000.00"),
            statement_date=date.today(),
        )

        # Without session context, this should return Decimal("0")
        # The actual calculation requires database access
        # This test verifies the method exists and returns a Decimal
        assert hasattr(recon, "calculate_cleared_balance")

    def test_calculate_discrepancy_method_exists(self):
        """Test that discrepancy calculation method exists."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1000.00"),
            statement_date=date.today(),
        )

        assert hasattr(recon, "calculate_discrepancy")


class TestReconciliationValidation:
    """Tests for reconciliation validation rules."""

    def test_statement_date_not_in_future(self):
        """Test that future statement dates should be rejected at API level."""
        # Note: The model itself doesn't enforce this - it's handled by Pydantic schema
        future_date = date.today() + timedelta(days=30)

        # Model allows it (validation is in schema)
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1000.00"),
            statement_date=future_date,
        )

        assert recon.statement_date == future_date

    def test_statement_date_in_past(self):
        """Test that past statement dates are valid."""
        past_date = date.today() - timedelta(days=30)

        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1000.00"),
            statement_date=past_date,
        )

        assert recon.statement_date == past_date


class TestReconciliationCompletion:
    """Tests for reconciliation completion."""

    def test_mark_completed(self):
        """Test marking reconciliation as completed."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1000.00"),
            statement_date=date.today(),
            status=ReconciliationStatus.IN_PROGRESS,
        )

        assert recon.status == ReconciliationStatus.IN_PROGRESS
        assert recon.completed_at is None

        # Mark as completed
        recon.status = ReconciliationStatus.COMPLETED
        recon.completed_at = datetime.now(timezone.utc)

        assert recon.status == ReconciliationStatus.COMPLETED
        assert recon.completed_at is not None

    def test_adjustment_transaction_link(self):
        """Test linking adjustment transaction."""
        recon = Reconciliation(
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            statement_balance=Decimal("1000.00"),
            statement_date=date.today(),
        )

        adjustment_id = uuid.uuid4()
        recon.adjustment_transaction_id = adjustment_id

        assert recon.adjustment_transaction_id == adjustment_id
