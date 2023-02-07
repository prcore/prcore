import logging
from random import choice
from string import ascii_letters, digits
from time import localtime, strftime

from fastapi import Request

# Enable logging
logger = logging.getLogger(__name__)


def get_current_time_label() -> str:
    # Get the current time label
    return strftime("%Y%m%d%H%M%S", localtime())


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


def random_str(i: int) -> str:
    # Get a random string
    return "".join(choice(ascii_letters + digits) for _ in range(i))
