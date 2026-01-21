"""
Unit tests for bank provider adapter factory.

Tests the get_bank_adapter factory function that returns
the appropriate adapter based on configuration.
"""
from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from mybudget.adapters import (
    BankProviderAdapter,
    EnableBankingAdapter,
    GoCardlessAdapter,
    MockBankAdapter,
    get_bank_adapter,
)


@pytest.fixture
def mock_private_key():
    """Create a temporary private key file for testing."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    # Generate a proper RSA key for testing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False) as f:
        f.write(key_bytes)
        return Path(f.name)


class TestGetBankAdapterFactory:
    """Tests for get_bank_adapter factory function."""

    def test_get_mock_adapter_default(self) -> None:
        """Test getting mock adapter when BANK_PROVIDER is 'mock'."""
        with patch("mybudget.adapters.settings") as mock_settings:
            mock_settings.BANK_PROVIDER = "mock"

            adapter = get_bank_adapter()

            assert isinstance(adapter, MockBankAdapter)
            assert adapter.provider_name == "mock"

    def test_get_mock_adapter_explicit(self) -> None:
        """Test getting mock adapter when explicitly specified."""
        adapter = get_bank_adapter("mock")

        assert isinstance(adapter, MockBankAdapter)
        assert adapter.provider_name == "mock"

    def test_get_gocardless_adapter(self) -> None:
        """Test getting GoCardless adapter."""
        with patch("mybudget.adapters.settings") as factory_settings, \
             patch("mybudget.adapters.gocardless_adapter.settings") as adapter_settings:
            factory_settings.BANK_PROVIDER = "gocardless"
            adapter_settings.GOCARDLESS_SECRET_ID = "test-id"
            adapter_settings.GOCARDLESS_SECRET_KEY = "test-key"
            adapter_settings.GOCARDLESS_BASE_URL = "https://api.gocardless.com"

            adapter = get_bank_adapter()

            assert isinstance(adapter, GoCardlessAdapter)
            assert adapter.provider_name == "gocardless"

    def test_get_gocardless_adapter_explicit(self) -> None:
        """Test getting GoCardless adapter when explicitly specified."""
        with patch("mybudget.adapters.gocardless_adapter.settings") as mock_settings:
            mock_settings.GOCARDLESS_SECRET_ID = "test-id"
            mock_settings.GOCARDLESS_SECRET_KEY = "test-key"
            mock_settings.GOCARDLESS_BASE_URL = "https://api.gocardless.com"

            adapter = get_bank_adapter("gocardless")

            assert isinstance(adapter, GoCardlessAdapter)
            assert adapter.provider_name == "gocardless"

    def test_get_enablebanking_adapter(self, mock_private_key) -> None:
        """Test getting EnableBanking adapter."""
        with patch("mybudget.adapters.settings") as factory_settings, \
             patch("mybudget.adapters.enablebanking_adapter.settings") as adapter_settings:
            factory_settings.BANK_PROVIDER = "enablebanking"
            adapter_settings.ENABLEBANKING_APP_ID = "test-app-id"
            adapter_settings.ENABLEBANKING_PRIVATE_KEY_PATH = str(mock_private_key)
            adapter_settings.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

            adapter = get_bank_adapter()

            assert isinstance(adapter, EnableBankingAdapter)
            assert adapter.provider_name == "enablebanking"

    def test_get_enablebanking_adapter_explicit(self, mock_private_key) -> None:
        """Test getting EnableBanking adapter when explicitly specified."""
        with patch("mybudget.adapters.enablebanking_adapter.settings") as mock_settings:
            mock_settings.ENABLEBANKING_APP_ID = "test-app-id"
            mock_settings.ENABLEBANKING_PRIVATE_KEY_PATH = str(mock_private_key)
            mock_settings.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

            adapter = get_bank_adapter("enablebanking")

            assert isinstance(adapter, EnableBankingAdapter)
            assert adapter.provider_name == "enablebanking"

    def test_unsupported_provider_raises_error(self) -> None:
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported bank provider"):
            get_bank_adapter("unsupported_provider")

    def test_adapter_returns_correct_interface(self) -> None:
        """Test that returned adapter implements BankProviderAdapter."""
        adapter = get_bank_adapter("mock")

        assert isinstance(adapter, BankProviderAdapter)
        assert hasattr(adapter, "get_institutions")
        assert hasattr(adapter, "create_requisition")
        assert hasattr(adapter, "get_accounts")
        assert hasattr(adapter, "get_transactions")

    def test_provider_override_ignores_settings(self, mock_private_key) -> None:
        """Test that explicit provider parameter overrides settings."""
        with patch("mybudget.adapters.settings") as factory_settings, \
             patch("mybudget.adapters.enablebanking_adapter.settings") as adapter_settings:
            # Settings say gocardless
            factory_settings.BANK_PROVIDER = "gocardless"
            # But we explicitly request enablebanking
            adapter_settings.ENABLEBANKING_APP_ID = "test-app-id"
            adapter_settings.ENABLEBANKING_PRIVATE_KEY_PATH = str(mock_private_key)
            adapter_settings.ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

            adapter = get_bank_adapter("enablebanking")

            # Should return EnableBanking despite settings
            assert isinstance(adapter, EnableBankingAdapter)
