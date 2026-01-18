"""
Structured logging configuration.

Configures structlog for JSON logging with context processors
for request tracing and structured output.
"""
import logging
import sys
from typing import Any

import structlog


def configure_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Args:
        json_logs: If True, output JSON logs. If False, output colored console logs.
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Set up standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Shared processors for all log entries
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # JSON output for production
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Colored console output for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Optional logger name. If not provided, uses the calling module.

    Returns:
        A configured structlog logger.
    """
    return structlog.get_logger(name)


# Pre-configured loggers for common use cases
def log_user_action(
    action: str,
    user_id: str | None = None,
    **kwargs: Any,
) -> None:
    """
    Log a user action for observability.

    Args:
        action: The action being performed (e.g., "login", "logout", "transaction_approved").
        user_id: The ID of the user performing the action.
        **kwargs: Additional context to include in the log.
    """
    logger = get_logger("user_actions")
    logger.info(
        action,
        user_id=user_id,
        **kwargs,
    )


def log_error(
    error: str,
    exc_info: bool = False,
    **kwargs: Any,
) -> None:
    """
    Log an error with context.

    Args:
        error: The error message.
        exc_info: Whether to include exception info.
        **kwargs: Additional context to include in the log.
    """
    logger = get_logger("errors")
    logger.error(error, exc_info=exc_info, **kwargs)
