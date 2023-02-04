import logging
from random import choice
from string import ascii_letters, digits
from time import localtime, strftime

# Enable logging
logger = logging.getLogger(__name__)


def get_current_time_label() -> str:
    # Get the current time label
    return strftime("%Y%m%d%H%M%S", localtime())


def random_str(i: int) -> str:
    # Get a random string
    return "".join(choice(ascii_letters + digits) for _ in range(i))
