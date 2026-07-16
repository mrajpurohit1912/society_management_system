import logging
import sys
import structlog
import queue
import threading
import time
import requests
from requests.auth import HTTPBasicAuth
from app.core.logging_context import get_logging_context

class LokiHandler(logging.Handler):
    """
    A custom, non-blocking log handler that pushes formatted log events to Grafana Loki
    in a background thread to prevent blocking the main application event loop.
    """
    def __init__(self, url: str, username: str, token: str, labels: dict = None):
        super().__init__()
        # Normalize Loki endpoint
        url = url.rstrip("/")
        if not url.endswith("/loki/api/v1/push"):
            url = f"{url}/loki/api/v1/push"
        self.url = url
        self.auth = HTTPBasicAuth(username, token)
        self.labels = labels or {"application": "society-management-backend"}
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Daemon thread to batch and send logs in the background
        self.worker = threading.Thread(target=self._post_loop, daemon=True)
        self.worker.start()

    def emit(self, record):
        try:
            log_entry = self.format(record)
            # Loki requires timestamps in nanoseconds as strings
            ns_timestamp = str(int(time.time() * 1e9))
            self.queue.put((ns_timestamp, log_entry))
        except Exception:
            self.handleError(record)

    def _post_loop(self):
        while not self.stop_event.is_set():
            batch = []
            try:
                # Wait for at least one log, timeout periodic to check stop_event
                item = self.queue.get(timeout=1.0)
                batch.append(item)
                
                # Batch up to 50 logs in one request
                while len(batch) < 50:
                    try:
                        batch.append(self.queue.get_nowait())
                    except queue.Empty:
                        break
            except queue.Empty:
                continue

            if batch:
                self._send_batch(batch)

    def _send_batch(self, batch):
        payload = {
            "streams": [
                {
                    "stream": self.labels,
                    "values": batch
                }
            ]
        }
        headers = {"Content-Type": "application/json"}
        try:
            # Direct HTTP POST without routing back through python logging to prevent infinite loops
            response = requests.post(
                self.url,
                json=payload,
                headers=headers,
                auth=self.auth,
                timeout=5.0
            )
            if response.status_code >= 400:
                sys.stderr.write(f"Loki push failed status={response.status_code}: {response.text}\n")
        except Exception as e:
            sys.stderr.write(f"Exception sending logs to Loki: {str(e)}\n")
        finally:
            for _ in batch:
                self.queue.task_done()

    def close(self):
        self.stop_event.set()
        super().close()

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

    # Add Loki Handler in production if configured
    from app.core.config import settings
    if settings.LOKI_URL and settings.LOKI_USER and settings.LOKI_TOKEN:
        loki_handler = LokiHandler(
            url=settings.LOKI_URL,
            username=settings.LOKI_USER,
            token=settings.LOKI_TOKEN,
            labels={"application": "society-management-backend", "env": env}
        )
        loki_handler.setFormatter(formatter)
        root_logger.addHandler(loki_handler)

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
