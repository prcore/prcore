import logging
from zipfile import ZipFile

from fastapi import HTTPException
from pandas import DataFrame, read_csv
from pm4py import read_xes

from core.confs import path
from core.functions.general.file import get_extension, get_new_path, delete_file

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_file(file_path: str, extension: str, separator: str) -> DataFrame:
    if extension == "xes":
        df = get_dataframe_from_xes(file_path)
    elif extension == "csv":
        df = get_dataframe_from_csv(file_path, separator)
    else:
        df = get_dataframe_from_zip(file_path, separator)
    return df


def get_dataframe_from_xes(file_path: str) -> DataFrame:
    # Get dataframe from xes file
    df = read_xes(file_path)
    df = df.astype(str)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df


def get_dataframe_from_csv(file_path: str, separator: str) -> DataFrame:
    # Get dataframe from csv file
    df = read_csv(file_path, sep=separator, dtype=str)
    df_obj = df.select_dtypes(["object"])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    return df


def get_dataframe_from_zip(file_path: str, separator: str) -> DataFrame | None:
    # Get dataframe from zip file
    result = None
    temp_path = ""

    try:
        with ZipFile(file_path) as zip_file:
            name_list = zip_file.namelist()

            if len(name_list) != 1:
                raise HTTPException(status_code=400, detail="Zip file should contain only one file")

            filename = name_list[0]
            extension = get_extension(filename)

            if extension not in path.ALLOWED_EXTRACTED_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Zip file should contain only xes or csv file")

            temp_path = get_new_path(base_path=f"{path.TEMP_PATH}/", suffix=f".{extension}")

            with open(temp_path, "wb") as f:
                f.write(zip_file.read(filename))

            if extension == "xes":
                result = get_dataframe_from_xes(temp_path)
            elif extension == "csv":
                result = get_dataframe_from_csv(temp_path, separator)
    except Exception as e:
        logger.warning(f"Get dataframe from zip error: {e}", exc_info=True)
        delete_file(file_path)
        raise e
    finally:
        delete_file(temp_path)

    return result
