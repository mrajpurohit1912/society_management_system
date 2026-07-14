import logging
import sys
import structlog
from app.core.logging_context import get_logging_context

def pii_masker_processor(logger, method_name, event_dict):
    """Masks sensitive data keys to prevent PII leakage in logs."""
    sensitive_keys = {
        "password", "secret", "token", "cvv", "card_number", 
        "auth_token", "otp", "jwt", "jwt_secret_key", "refresh_token"
    }
    # Create a copy or list to avoid mutating during iteration
    for key in list(event_dict.keys()):
        if any(sk in key.lower() for sk in sensitive_keys):
            event_dict[key] = "********"
    return event_dict

def inject_context_processor(logger, method_name, event_dict):
    """Injects request-scoped context variables into the log event."""
    context = get_logging_context()
    for k, v in context.items():
        if k not in event_dict:
            event_dict[k] = v
    return event_dict

def setup_logging(env: str = "production", log_level: str = "INFO"):
    """
    Configures Python standard logging and structlog to unify log formatting.
    In production, logs are formatted as structured JSON.
    In local development, logs are pretty-printed with console colors.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Core shared processors run for all log messages
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        inject_context_processor,
        pii_masker_processor,
    ]

    if env == "production":
        # Production uses structured JSON output
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
        )
    else:
        # Development uses colorized pretty output
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )

    # Configure handler for root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate logs in the console
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # Configure structlog to route through stdlib
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure third-party loggers levels
    if env == "production":
        # Keep third-party noise low in production
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    else:
        # Allow standard uvicorn info log in development
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
