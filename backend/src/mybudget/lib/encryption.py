"""
Token encryption utilities for secure storage of bank credentials.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
"""
from cryptography.fernet import Fernet, InvalidToken

from mybudget.config import settings


class EncryptionError(Exception):
    """Base exception for encryption errors."""

    pass


class EncryptionKeyNotConfigured(EncryptionError):
    """Raised when encryption key is not configured."""

    pass


class DecryptionError(EncryptionError):
    """Raised when decryption fails (invalid token or wrong key)."""

    pass


def _get_fernet() -> Fernet:
    """Get Fernet instance with configured key.

    Returns:
        Configured Fernet instance.

    Raises:
        EncryptionKeyNotConfigured: If BANK_TOKEN_ENCRYPTION_KEY is not set.
    """
    key = settings.BANK_TOKEN_ENCRYPTION_KEY
    if not key:
        raise EncryptionKeyNotConfigured(
            "BANK_TOKEN_ENCRYPTION_KEY environment variable is not configured. "
            "Generate a key with: python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode())


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token for secure storage.

    Args:
        plaintext: The plain text token to encrypt.

    Returns:
        Base64-encoded encrypted token.

    Raises:
        EncryptionKeyNotConfigured: If encryption key is not set.
        EncryptionError: If encryption fails for any other reason.
    """
    if not plaintext:
        raise EncryptionError("Cannot encrypt empty token")

    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return encrypted.decode()
    except EncryptionKeyNotConfigured:
        raise
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a previously encrypted token.

    Args:
        ciphertext: The Base64-encoded encrypted token.

    Returns:
        The original plain text token.

    Raises:
        EncryptionKeyNotConfigured: If encryption key is not set.
        DecryptionError: If decryption fails (invalid token or wrong key).
    """
    if not ciphertext:
        raise DecryptionError("Cannot decrypt empty ciphertext")

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except EncryptionKeyNotConfigured:
        raise
    except InvalidToken as e:
        raise DecryptionError(
            "Decryption failed: invalid token. "
            "The token may be corrupted or encrypted with a different key."
        ) from e
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        A new Base64-encoded Fernet key suitable for BANK_TOKEN_ENCRYPTION_KEY.
    """
    return Fernet.generate_key().decode()
