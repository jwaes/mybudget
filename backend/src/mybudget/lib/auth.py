"""
Authentication utility functions for MyBudget.

Provides password hashing and verification using Argon2id, which is the
recommended algorithm for password storage.
"""

from pwdlib import PasswordHash

# Configure Argon2id hasher with secure defaults
_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string (includes salt and parameters).
    """
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: The plain text password to verify.
        hashed: The hashed password to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    return _hasher.verify(password, hashed)
