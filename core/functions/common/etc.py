import logging
import re
from datetime import datetime
from multiprocessing import cpu_count, Process
from random import choice
from string import ascii_letters, digits
from threading import active_count, Thread, Timer
from time import localtime, strftime
from typing import Callable, Tuple, Any

# Enable logging
logger = logging.getLogger(__name__)


def delay(secs: int, target: Callable, args: list = None) -> bool:
    # Call a function with delay
    result = False

    try:
        t = Timer(secs, target, args)
        t.daemon = True
        result = t.start() or True
    except Exception as e:
        logger.warning(f"Delay error: {e}", exc_info=True)

    return result


def get_current_time_label() -> str:
    # Get the current time label
    return strftime("%Y%m%d%H%M%S", localtime())


def get_readable_time(secs: int = 0, the_format: str = "%Y%m%d%H%M%S") -> str:
    # Get a readable time string
    result = ""

    try:
        if secs:
            result = datetime.utcfromtimestamp(secs).strftime(the_format)
        else:
            result = strftime(the_format, localtime())
    except Exception as e:
        logger.warning(f"Get readable time error: {e}", exc_info=True)

    return result


def get_message_id() -> str:
    # Get a message id
    return f"{get_current_time_label()}-{random_str(16)}"


def get_processes_number() -> int:
    return cpu_count()


def process_daemon(target: Callable, args: Tuple) -> None:
    # Process daemon
    p = Process(target=target, args=args)
    p.daemon = True
    p.start()


def random_str(i: int) -> str:
    # Get a random string
    return "".join(choice(ascii_letters + digits) for _ in range(i))


def thread(target: Callable, args: Tuple, kwargs: dict = None, daemon: bool = True) -> bool:
    # Call a function using thread
    result = False

    try:
        t = Thread(target=target, args=args, kwargs=kwargs, daemon=daemon, name=f"{target.__name__}-{random_str(8)}")
        t.daemon = daemon
        result = t.start() or True
    except Exception as e:
        logger.warning(f"Thread error: {e}", exc_info=True)
        logger.warning(f"Current threads: {active_count()}")

    return result


def convert_to_seconds(time_str: Any):
    time_str = str(time_str).strip().lower()
    if time_str.isdigit():
        return int(time_str)

    match = re.match(r"^(\d+)\s*(\w+)$", time_str)
    if not match:
        raise ValueError("Invalid input")

    value = int(match.group(1))
    unit = match.group(2)

    if unit in ["months", "month", "mo", "m"]:
        return value * 30 * 24 * 60 * 60
    elif unit in ["weeks", "week", "wk", "w"]:
        return value * 7 * 24 * 60 * 60
    elif unit in ["days", "day", "d"]:
        return value * 24 * 60 * 60
    elif unit in ["hours", "hour", "hr", "h"]:
        return value * 60 * 60
    elif unit in ["minutes", "minute", "min", "m"]:
        return value * 60
    elif unit in ["seconds", "second", "sec", "s"]:
        return value
    else:
        raise ValueError("Invalid unit")
