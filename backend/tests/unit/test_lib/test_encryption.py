"""
Unit tests for token encryption utilities.
"""
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from mybudget.lib.encryption import (
    DecryptionError,
    EncryptionError,
    EncryptionKeyNotConfigured,
    decrypt_token,
    encrypt_token,
    generate_encryption_key,
)


# Generate a valid test key
TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()


class TestEncryptToken:
    """Tests for encrypt_token function."""

    def test_encrypt_token_success(self) -> None:
        """Test encrypting a token successfully."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "my-secret-access-token"
            ciphertext = encrypt_token(plaintext)

            # Ciphertext should be different from plaintext
            assert ciphertext != plaintext
            # Ciphertext should be Base64-encoded (Fernet format)
            assert ciphertext.startswith("gAAAAA")

    def test_encrypt_token_different_each_time(self) -> None:
        """Test that encrypting the same token produces different ciphertext."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "my-secret-access-token"
            ciphertext1 = encrypt_token(plaintext)
            ciphertext2 = encrypt_token(plaintext)

            # Due to Fernet's random IV, same plaintext produces different ciphertext
            assert ciphertext1 != ciphertext2

    def test_encrypt_token_no_key_configured(self) -> None:
        """Test encryption fails when key is not configured."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = None

            with pytest.raises(EncryptionKeyNotConfigured) as exc_info:
                encrypt_token("some-token")

            assert "BANK_TOKEN_ENCRYPTION_KEY" in str(exc_info.value)

    def test_encrypt_token_empty_plaintext(self) -> None:
        """Test encryption fails with empty plaintext."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            with pytest.raises(EncryptionError, match="Cannot encrypt empty token"):
                encrypt_token("")


class TestDecryptToken:
    """Tests for decrypt_token function."""

    def test_decrypt_token_success(self) -> None:
        """Test decrypting a token successfully."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "my-secret-access-token"
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext

    def test_decrypt_token_complex_content(self) -> None:
        """Test encrypting and decrypting complex content."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            # Test with various characters
            plaintext = '{"access_token": "abc123", "refresh_token": "xyz789"}'
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext

    def test_decrypt_token_unicode(self) -> None:
        """Test encrypting and decrypting unicode content."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "token-with-unicode-\u00e9\u00e8\u00ea"
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext

    def test_decrypt_token_no_key_configured(self) -> None:
        """Test decryption fails when key is not configured."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = None

            with pytest.raises(EncryptionKeyNotConfigured) as exc_info:
                decrypt_token("some-ciphertext")

            assert "BANK_TOKEN_ENCRYPTION_KEY" in str(exc_info.value)

    def test_decrypt_token_empty_ciphertext(self) -> None:
        """Test decryption fails with empty ciphertext."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            with pytest.raises(DecryptionError, match="Cannot decrypt empty ciphertext"):
                decrypt_token("")

    def test_decrypt_token_invalid_ciphertext(self) -> None:
        """Test decryption fails with invalid ciphertext."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            with pytest.raises(DecryptionError, match="invalid token"):
                decrypt_token("not-a-valid-encrypted-token")

    def test_decrypt_token_wrong_key(self) -> None:
        """Test decryption fails when using wrong key."""
        different_key = Fernet.generate_key().decode()

        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "my-secret-access-token"
            ciphertext = encrypt_token(plaintext)

        # Try decrypting with a different key
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = different_key

            with pytest.raises(DecryptionError, match="invalid token"):
                decrypt_token(ciphertext)

    def test_decrypt_token_tampered_ciphertext(self) -> None:
        """Test decryption fails when ciphertext is tampered with."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "my-secret-access-token"
            ciphertext = encrypt_token(plaintext)

            # Tamper with the ciphertext (change a character)
            tampered = ciphertext[:-5] + "XXXXX"

            with pytest.raises(DecryptionError, match="invalid token"):
                decrypt_token(tampered)


class TestGenerateEncryptionKey:
    """Tests for generate_encryption_key function."""

    def test_generate_encryption_key_returns_valid_key(self) -> None:
        """Test that generated key is valid Fernet key."""
        key = generate_encryption_key()

        # Should be able to create Fernet with this key
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_generate_encryption_key_different_each_time(self) -> None:
        """Test that each call generates a different key."""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        assert key1 != key2

    def test_generated_key_can_be_used(self) -> None:
        """Test that a generated key can be used for encryption/decryption."""
        key = generate_encryption_key()

        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = key

            plaintext = "test-token"
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext


class TestEdgeCases:
    """Edge case tests for encryption utilities."""

    def test_very_long_token(self) -> None:
        """Test encrypting and decrypting a very long token."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            # Create a 10KB token
            plaintext = "x" * 10240
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext

    def test_token_with_special_characters(self) -> None:
        """Test encrypting token with special characters."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "token!@#$%^&*()_+-=[]{}|;':\",./<>?"
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext

    def test_token_with_newlines(self) -> None:
        """Test encrypting token with newlines."""
        with patch("mybudget.lib.encryption.settings") as mock_settings:
            mock_settings.BANK_TOKEN_ENCRYPTION_KEY = TEST_ENCRYPTION_KEY

            plaintext = "line1\nline2\rline3\r\nline4"
            ciphertext = encrypt_token(plaintext)
            decrypted = decrypt_token(ciphertext)

            assert decrypted == plaintext
