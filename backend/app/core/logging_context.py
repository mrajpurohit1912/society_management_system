import contextvars
from typing import Dict, Any

# ContextVar is async-safe and thread-safe. It keeps variables scoped to the current execution context.
_request_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "request_context", default={}
)

def set_logging_context(**kwargs: Any) -> None:
    """Sets contextual values for the current request scope."""
    ctx = _request_context.get().copy()
    ctx.update(kwargs)
    _request_context.set(ctx)

def get_logging_context() -> Dict[str, Any]:
    """Retrieves the current logging context."""
    return _request_context.get()

def clear_logging_context() -> None:
    """Clears the logging context."""
    _request_context.set({})
