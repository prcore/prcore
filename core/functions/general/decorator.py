import logging
from functools import wraps

from core.functions.general.etc import thread

# Enable logging
logger = logging.getLogger(__name__)


def threaded(daemon: bool = True):
    # Run with thread
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return thread(func, args, kwargs, daemon)
        return wrapper
    return decorator
