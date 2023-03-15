import logging
from os import remove
from os.path import exists
from shutil import copy, move, rmtree
from typing import Optional

from pandas import DataFrame, read_pickle

from core.confs import path
from core.functions.common.etc import random_str

# Enable logging
logger = logging.getLogger(__name__)


def copy_file(src: str, dst: str) -> bool:
    # Copy a file
    result = False

    try:
        if not(src and exists(src)):
            return False

        copy(src, dst)
        result = True
    except Exception as e:
        logger.warning(f"Copy file error: {e}", exc_info=True)

    return result


def delete_file(file_path: str) -> bool:
    # Delete a file
    result = False

    try:
        if not(file_path and exists(file_path)):
            return False

        try:
            remove(file_path)
        except IsADirectoryError:
            rmtree(file_path)

        result = True
    except Exception as e:
        logger.warning(f"Delete file error: {e}", exc_info=True)

    return result


def get_extension(file_name: str) -> str:
    # Get the extension of a file name
    result = ""

    try:
        result = result if "." not in file_name else file_name.split(".")[-1]
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


def move_file(src: str, dst: str) -> bool:
    # Move a file
    result = False

    try:
        if not src or not exists(src) or not dst:
            return False

        result = bool(move(src, dst))
    except Exception as e:
        logger.warning(f"Move file error: {e}", exc_info=True)

    return result


def get_dataframe_from_pickle(df_path: str) -> Optional[DataFrame]:
    # Get dataframe from pickle file
    return read_pickle(df_path)


def save_dataframe_to_pickle(df_path: str, df: DataFrame) -> None:
    # Save dataframe to pickle file
    df.to_pickle(df_path)
