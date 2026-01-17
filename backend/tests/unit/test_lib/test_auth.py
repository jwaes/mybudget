"""
Unit tests for authentication utilities (password hashing).
"""
import pytest

from mybudget.lib.auth import hash_password, verify_password


@pytest.mark.unit
class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_hash(self) -> None:
        """Test that hash_password returns a hashed string."""
        password = "test_password123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 50  # Argon2 hashes are long
        assert hashed != password  # Hash should be different from plain text

    def test_hash_password_different_each_time(self) -> None:
        """Test that hashing same password twice gives different hashes (salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Salted hashes should differ

    def test_verify_password_correct(self) -> None:
        """Test that verify_password returns True for correct password."""
        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """Test that verify_password returns False for incorrect password."""
        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_case_sensitive(self) -> None:
        """Test that password verification is case-sensitive."""
        password = "MyPassword123"
        hashed = hash_password(password)

        assert verify_password("mypassword123", hashed) is False
        assert verify_password("MYPASSWORD123", hashed) is False
        assert verify_password("MyPassword123", hashed) is True

    def test_hash_empty_password(self) -> None:
        """Test that empty password can be hashed (validation should be elsewhere)."""
        password = ""
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_long_password(self) -> None:
        """Test hashing a very long password."""
        password = "a" * 1000
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True

    def test_hash_special_characters(self) -> None:
        """Test hashing password with special characters."""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_unicode_password(self) -> None:
        """Test hashing password with unicode characters."""
        password = "пароль密码🔐"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
