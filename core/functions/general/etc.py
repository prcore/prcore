import logging
import re
from datetime import datetime
from hashlib import md5
from html import escape
from json import dumps
from random import choice, uniform
from string import ascii_letters, digits
from threading import active_count, Thread, Timer
from time import gmtime, localtime, mktime, sleep, strftime, time
from typing import Any, Callable, Optional, Union
from unicodedata import normalize

# Enable logging
logger = logging.getLogger(__name__)


def random_str(i: int) -> str:
    # Get a random string
    result = ""

    try:
        result = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        logger.warning(f"Random str error: {e}", exc_info=True)

    return result
