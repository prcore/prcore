import logging
from datetime import datetime
from multiprocessing import Process
from random import choice
from string import ascii_letters, digits
from threading import active_count, Thread
from time import localtime, strftime

from fastapi import Request

# Enable logging
logger = logging.getLogger(__name__)


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


def get_real_ip(request: Request) -> str:
    # Get the real ip address of the client
    result = ""

    try:
        result = request.headers.get("X-Forwarded-For")

        if not result:
            return request.client.host

        if "," not in result:
            return result

        result = result.split(",")[0]
    except Exception as e:
        logger.warning(f"Get real ip error: {e}", exc_info=True)

    return result


def process_daemon(func: callable, args: tuple = ()) -> Process:
    # Process daemon
    p = Process(target=func, args=args)
    p.daemon = True
    p.start()
    return p


def random_str(i: int) -> str:
    # Get a random string
    return "".join(choice(ascii_letters + digits) for _ in range(i))


def thread(target: callable, args: tuple, kwargs: dict = None, daemon: bool = True) -> bool:
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
