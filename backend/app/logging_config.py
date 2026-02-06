"""
Structured logging configuration using structlog.

Provides JSON-formatted logs for production environments with
context-aware logging for agents, API requests, and email operations.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Args:
        json_logs: If True, output JSON format (for production).
                   If False, output colored console format (for development).
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    # Shared processors for all log entries
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Production: JSON output
        shared_processors.append(structlog.processors.format_exc_info)
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Development: Colored console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger for a module.

    Usage:
        logger = get_logger(__name__)
        logger.info("message", key="value")
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables to all subsequent log entries in this context.

    Usage:
        bind_context(agent_id=1, site_id=5)
        logger.info("processing site")  # Will include agent_id and site_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


# Pre-configured loggers for common use cases
class AgentLogger:
    """Logger with agent-specific context."""

    def __init__(self, agent_id: int, agent_name: str):
        self.logger = get_logger("agent")
        self.agent_id = agent_id
        self.agent_name = agent_name

    def _with_context(self, **kwargs: Any) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            **kwargs
        }

    def info(self, msg: str, **kwargs: Any) -> None:
        self.logger.info(msg, **self._with_context(**kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        self.logger.warning(msg, **self._with_context(**kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        self.logger.error(msg, **self._with_context(**kwargs))

    def debug(self, msg: str, **kwargs: Any) -> None:
        self.logger.debug(msg, **self._with_context(**kwargs))


class EmailLogger:
    """Logger for email operations."""

    def __init__(self):
        self.logger = get_logger("email")

    def sent(self, recipient: str, subject: str, message_id: str = None, **kwargs: Any) -> None:
        self.logger.info(
            "email_sent",
            recipient=recipient,
            subject=subject,
            message_id=message_id,
            **kwargs
        )

    def failed(self, recipient: str, subject: str, error: str, **kwargs: Any) -> None:
        self.logger.error(
            "email_failed",
            recipient=recipient,
            subject=subject,
            error=error,
            **kwargs
        )

    def received(self, sender: str, subject: str, **kwargs: Any) -> None:
        self.logger.info(
            "email_received",
            sender=sender,
            subject=subject,
            **kwargs
        )


class APILogger:
    """Logger for API requests."""

    def __init__(self):
        self.logger = get_logger("api")

    def request(self, method: str, path: str, user: str = None, **kwargs: Any) -> None:
        self.logger.info(
            "api_request",
            method=method,
            path=path,
            user=user,
            **kwargs
        )

    def response(self, method: str, path: str, status_code: int, duration_ms: float = None, **kwargs: Any) -> None:
        self.logger.info(
            "api_response",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
