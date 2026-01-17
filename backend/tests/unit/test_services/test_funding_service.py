"""
Unit tests for FundingService.

Tests funding operations: fund single category, fund all, partial funding.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mybudget.services.funding_service import FundingService, FundingResult
from mybudget.models.target import TargetType


class TestFundingServiceInit:
    """Tests for FundingService initialization."""

    def test_init_with_db_session(self) -> None:
        """Test FundingService can be initialized with db session."""
        mock_db = MagicMock()
        service = FundingService(mock_db)
        assert service.db == mock_db


class TestFundSingleCategory:
    """Tests for fund_single_category (T145)."""

    @pytest.mark.asyncio
    async def test_fund_category_full_amount(self) -> None:
        """Test funding a single category when To Assign is sufficient."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        # Mock dependencies
        with patch.object(
            service, "_get_category_underfunded", new_callable=AsyncMock
        ) as mock_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_underfunded.return_value = Decimal("150.00")
            mock_to_assign.return_value = Decimal("500.00")
            mock_assign.return_value = MagicMock(
                id=uuid4(), amount=Decimal("150.00")
            )

            result = await service.fund_single_category(
                user_id=user_id,
                category_id=category_id,
                month=month,
            )

            assert result.funded_amount == Decimal("150.00")
            assert result.requested_amount == Decimal("150.00")
            assert result.is_partial is False
            mock_assign.assert_called_once_with(
                user_id, category_id, Decimal("150.00"), month
            )

    @pytest.mark.asyncio
    async def test_fund_category_partial_when_insufficient(self) -> None:
        """Test partial funding when To Assign is less than underfunded."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        with patch.object(
            service, "_get_category_underfunded", new_callable=AsyncMock
        ) as mock_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_underfunded.return_value = Decimal("500.00")
            mock_to_assign.return_value = Decimal("200.00")  # Insufficient
            mock_assign.return_value = MagicMock(
                id=uuid4(), amount=Decimal("200.00")
            )

            result = await service.fund_single_category(
                user_id=user_id,
                category_id=category_id,
                month=month,
            )

            assert result.funded_amount == Decimal("200.00")
            assert result.requested_amount == Decimal("500.00")
            assert result.is_partial is True
            mock_assign.assert_called_once_with(
                user_id, category_id, Decimal("200.00"), month
            )

    @pytest.mark.asyncio
    async def test_fund_category_zero_when_no_to_assign(self) -> None:
        """Test no funding when To Assign is zero."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        with patch.object(
            service, "_get_category_underfunded", new_callable=AsyncMock
        ) as mock_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_underfunded.return_value = Decimal("500.00")
            mock_to_assign.return_value = Decimal("0.00")

            result = await service.fund_single_category(
                user_id=user_id,
                category_id=category_id,
                month=month,
            )

            assert result.funded_amount == Decimal("0.00")
            assert result.requested_amount == Decimal("500.00")
            assert result.is_partial is True
            mock_assign.assert_not_called()

    @pytest.mark.asyncio
    async def test_fund_category_zero_when_already_funded(self) -> None:
        """Test no funding when category is already fully funded."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        category_id = uuid4()
        month = date(2026, 1, 1)

        with patch.object(
            service, "_get_category_underfunded", new_callable=AsyncMock
        ) as mock_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_underfunded.return_value = Decimal("0.00")  # Already funded
            mock_to_assign.return_value = Decimal("500.00")

            result = await service.fund_single_category(
                user_id=user_id,
                category_id=category_id,
                month=month,
            )

            assert result.funded_amount == Decimal("0.00")
            assert result.requested_amount == Decimal("0.00")
            assert result.is_partial is False
            mock_assign.assert_not_called()


class TestFundAllWithPriorityOrder:
    """Tests for fund_all_underfunded with priority order (T146)."""

    @pytest.mark.asyncio
    async def test_fund_all_when_sufficient_funds(self) -> None:
        """Test funding all underfunded categories when To Assign is enough."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        cat1_id = uuid4()
        cat2_id = uuid4()
        cat3_id = uuid4()

        underfunded_categories = [
            {"category_id": cat1_id, "category_name": "Rent", "underfunded": Decimal("100.00"), "priority": 0},
            {"category_id": cat2_id, "category_name": "Utilities", "underfunded": Decimal("200.00"), "priority": 1},
            {"category_id": cat3_id, "category_name": "Groceries", "underfunded": Decimal("150.00"), "priority": 2},
        ]

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_all_underfunded.return_value = underfunded_categories
            mock_to_assign.return_value = Decimal("1000.00")  # More than enough
            mock_assign.return_value = MagicMock(id=uuid4())

            result = await service.fund_all_underfunded(
                user_id=user_id,
                month=month,
            )

            assert result.total_funded == Decimal("450.00")
            assert result.total_underfunded == Decimal("450.00")
            assert result.categories_funded == 3
            assert result.is_partial is False
            assert mock_assign.call_count == 3

    @pytest.mark.asyncio
    async def test_fund_all_respects_priority_order(self) -> None:
        """Test that funding happens in priority order (group display_order)."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        cat1_id = uuid4()  # Priority 0 (first group)
        cat2_id = uuid4()  # Priority 1 (second group)
        cat3_id = uuid4()  # Priority 2 (third group)

        underfunded_categories = [
            {"category_id": cat1_id, "category_name": "Rent", "underfunded": Decimal("300.00"), "priority": 0},
            {"category_id": cat2_id, "category_name": "Utilities", "underfunded": Decimal("300.00"), "priority": 1},
            {"category_id": cat3_id, "category_name": "Groceries", "underfunded": Decimal("300.00"), "priority": 2},
        ]

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_all_underfunded.return_value = underfunded_categories
            # Only enough for first two categories
            mock_to_assign.return_value = Decimal("500.00")
            mock_assign.return_value = MagicMock(id=uuid4())

            result = await service.fund_all_underfunded(
                user_id=user_id,
                month=month,
            )

            # Should fund cat1 fully (300), cat2 partially (200), cat3 nothing
            assert result.total_funded == Decimal("500.00")
            assert result.total_underfunded == Decimal("900.00")
            assert result.categories_funded == 2  # cat3 gets nothing
            assert result.is_partial is True

            # Verify priority order in calls
            calls = mock_assign.call_args_list
            assert len(calls) == 2
            # First call should be cat1 with 300
            assert calls[0][0][1] == cat1_id
            assert calls[0][0][2] == Decimal("300.00")
            # Second call should be cat2 with 200 (remaining amount)
            assert calls[1][0][1] == cat2_id
            assert calls[1][0][2] == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_fund_all_nothing_underfunded(self) -> None:
        """Test fund all when nothing is underfunded."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_all_underfunded.return_value = []  # Nothing underfunded
            mock_to_assign.return_value = Decimal("500.00")

            result = await service.fund_all_underfunded(
                user_id=user_id,
                month=month,
            )

            assert result.total_funded == Decimal("0.00")
            assert result.total_underfunded == Decimal("0.00")
            assert result.categories_funded == 0
            assert result.is_partial is False
            mock_assign.assert_not_called()


class TestPartialFundingWhenInsufficient:
    """Tests for partial funding scenarios (T147)."""

    @pytest.mark.asyncio
    async def test_partial_fund_all_distributes_available(self) -> None:
        """Test that partial funding distributes what's available by priority."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        cat1_id = uuid4()
        cat2_id = uuid4()

        underfunded_categories = [
            {"category_id": cat1_id, "category_name": "Rent", "underfunded": Decimal("400.00"), "priority": 0},
            {"category_id": cat2_id, "category_name": "Utilities", "underfunded": Decimal("400.00"), "priority": 1},
        ]

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_all_underfunded.return_value = underfunded_categories
            mock_to_assign.return_value = Decimal("500.00")  # 300 short
            mock_assign.return_value = MagicMock(id=uuid4())

            result = await service.fund_all_underfunded(
                user_id=user_id,
                month=month,
            )

            # First category gets 400, second gets 100
            assert result.total_funded == Decimal("500.00")
            assert result.is_partial is True

            calls = mock_assign.call_args_list
            assert calls[0][0][2] == Decimal("400.00")  # cat1 full
            assert calls[1][0][2] == Decimal("100.00")  # cat2 partial

    @pytest.mark.asyncio
    async def test_no_assignment_created_when_zero_to_assign(self) -> None:
        """Test that no assignments are created when To Assign is zero."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        cat1_id = uuid4()
        underfunded_categories = [
            {"category_id": cat1_id, "category_name": "Rent", "underfunded": Decimal("400.00"), "priority": 0},
        ]

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded, patch.object(
            service, "_get_to_assign", new_callable=AsyncMock
        ) as mock_to_assign, patch.object(
            service, "_create_assignment", new_callable=AsyncMock
        ) as mock_assign:
            mock_all_underfunded.return_value = underfunded_categories
            mock_to_assign.return_value = Decimal("0.00")

            result = await service.fund_all_underfunded(
                user_id=user_id,
                month=month,
            )

            assert result.total_funded == Decimal("0.00")
            assert result.is_partial is True
            mock_assign.assert_not_called()


class TestGetUnderfundedSummary:
    """Tests for underfunded summary calculation."""

    @pytest.mark.asyncio
    async def test_get_underfunded_summary(self) -> None:
        """Test getting summary of all underfunded categories."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        cat1_id = uuid4()
        cat2_id = uuid4()

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded:
            mock_all_underfunded.return_value = [
                {
                    "category_id": cat1_id,
                    "category_name": "Groceries",
                    "underfunded": Decimal("150.00"),
                    "priority": 0,
                },
                {
                    "category_id": cat2_id,
                    "category_name": "Utilities",
                    "underfunded": Decimal("75.00"),
                    "priority": 1,
                },
            ]

            result = await service.get_underfunded_summary(
                user_id=user_id,
                month=month,
            )

            assert result["total_underfunded"] == Decimal("225.00")
            assert len(result["categories"]) == 2
            assert result["categories"][0]["category_name"] == "Groceries"
            assert result["categories"][0]["underfunded"] == Decimal("150.00")

    @pytest.mark.asyncio
    async def test_get_underfunded_summary_empty(self) -> None:
        """Test summary when nothing is underfunded."""
        mock_db = AsyncMock()
        service = FundingService(mock_db)

        user_id = uuid4()
        month = date(2026, 1, 1)

        with patch.object(
            service, "_get_all_underfunded", new_callable=AsyncMock
        ) as mock_all_underfunded:
            mock_all_underfunded.return_value = []

            result = await service.get_underfunded_summary(
                user_id=user_id,
                month=month,
            )

            assert result["total_underfunded"] == Decimal("0.00")
            assert len(result["categories"]) == 0


class TestFundingResult:
    """Tests for FundingResult data class."""

    def test_funding_result_creation(self) -> None:
        """Test FundingResult can be created."""
        result = FundingResult(
            funded_amount=Decimal("100.00"),
            requested_amount=Decimal("150.00"),
            is_partial=True,
        )
        assert result.funded_amount == Decimal("100.00")
        assert result.requested_amount == Decimal("150.00")
        assert result.is_partial is True

    def test_funding_result_full_funding(self) -> None:
        """Test FundingResult for full funding."""
        result = FundingResult(
            funded_amount=Decimal("150.00"),
            requested_amount=Decimal("150.00"),
            is_partial=False,
        )
        assert result.is_partial is False
