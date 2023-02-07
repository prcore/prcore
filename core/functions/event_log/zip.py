import logging
from zipfile import ZipFile

from fastapi import HTTPException
from pandas import DataFrame

from core import confs
from core.functions.event_log.csv import get_dataframe_from_csv
from core.functions.event_log.xes import get_dataframe_from_xes
from core.functions.general.file import delete_file, get_extension, get_new_path

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_zip(path: str, seperator: str) -> DataFrame | None:
    # Get dataframe from zip file
    result = None
    temp_path = ""

    try:
        with ZipFile(path) as zip_file:
            name_list = zip_file.namelist()

            if len(name_list) != 1:
                raise HTTPException(status_code=400, detail="Zip file should contain only one file")

            filename = name_list[0]
            extension = get_extension(filename)

            if extension not in confs.ALLOWED_EXTRACTED_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Zip file should contain only xes or csv file")

            temp_path = get_new_path(base_path=f"{confs.TEMP_PATH}/", suffix=f".{extension}")

            with open(temp_path, "wb") as f:
                f.write(zip_file.read(filename))

            if extension == "xes":
                result = get_dataframe_from_xes(temp_path)
            elif extension == "csv":
                result = get_dataframe_from_csv(temp_path, seperator)
    except Exception as e:
        logger.warning(f"Get dataframe from zip error: {e}", exc_info=True)
        delete_file(path)
        raise e
    finally:
        delete_file(temp_path)

    return result
