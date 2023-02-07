import logging
from os import remove
from os.path import exists

from core.functions.general.etc import random_str

# Enable logging
logger = logging.getLogger(__name__)


def delete_file(path: str) -> bool:
    # Delete a file
    result = False

    try:
        if not(path and exists(path)):
            return False

        result = remove(path) or True
    except Exception as e:
        logger.warning(f"Delete file error: {e}", exc_info=True)

    return result


def get_extension(path: str) -> str:
    # Get the extension of a file
    result = ""

    try:
        result = result if "." not in path else path.split(".")[-1]
        result = result.lower()
    except Exception as e:
        logger.warning(f"Get extension error: {e}", exc_info=True)

    return result


def get_new_path(base_path: str, prefix: str = "", suffix: str = "") -> str:
    # Get a new path in tmp directory
    result = ""

    try:
        if not base_path.endswith("/"):
            base_path += "/"

        file_path = random_str(8)

        while exists(f"{base_path}{prefix}{file_path}{suffix}"):
            file_path = random_str(8)

        result = f"{base_path}{prefix}{file_path}{suffix}"
    except Exception as e:
        logger.warning(f"Get new path error: {e}", exc_info=True)

    return result
