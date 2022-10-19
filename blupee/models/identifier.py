import logging
from random import randint

from blupee import glovar

# Enable logging
logger = logging.getLogger(__name__)


def get_identifier() -> int:
    # Get a random id

    result = 0

    try:
        result = glovar.identifiers.pop()
    except Exception as e:
        logger.warning(f"Get identifier error: {e}", exc_info=True)

    return result
