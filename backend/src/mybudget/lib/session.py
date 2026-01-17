"""
Session management utilities for MyBudget.

Provides cookie-based session management with signed tokens.
"""

import uuid

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from mybudget.config import settings


def _get_serializer() -> URLSafeTimedSerializer:
    """Get configured serializer for session tokens."""
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="session")


def create_session_token(user_id: uuid.UUID) -> str:
    """
    Create a signed session token for a user.

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        A signed token string containing the user ID.
    """
    serializer = _get_serializer()
    return serializer.dumps(str(user_id))


def validate_session_token(token: str) -> uuid.UUID | None:
    """
    Validate a session token and extract the user ID.

    Args:
        token: The signed session token.

    Returns:
        The user UUID if valid, None if invalid or expired.
    """
    serializer = _get_serializer()
    max_age = settings.SESSION_LIFETIME_MINUTES * 60  # Convert to seconds

    try:
        user_id_str = serializer.loads(token, max_age=max_age)
        return uuid.UUID(user_id_str)
    except (BadSignature, SignatureExpired, ValueError):
        return None


# Cookie configuration constants
SESSION_COOKIE_NAME = "session"
SESSION_COOKIE_MAX_AGE = settings.SESSION_LIFETIME_MINUTES * 60  # In seconds
SESSION_COOKIE_SECURE = settings.ENVIRONMENT not in ("development", "test")  # HTTPS only in prod
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "lax"
