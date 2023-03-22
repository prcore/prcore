import logging
from gzip import GzipFile
from zipfile import ZipFile

from fastapi import HTTPException
from pandas import DataFrame, read_csv
from pm4py import read_xes

from core.confs import path
from core.enums.error import ErrorType
from core.functions.common.file import get_extension, get_new_path, delete_file

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_file(file_path: str, extension: str, separator: str) -> DataFrame:
    if extension == "xes":
        df = get_dataframe_from_xes(file_path)
    elif extension == "csv":
        df = get_dataframe_from_csv(file_path, separator)
    else:
        df = get_dataframe_from_compressed_file(file_path, separator)
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


def get_dataframe_from_compressed_file(file_path: str, separator: str) -> DataFrame | None:
    # Get dataframe from compressed file
    try:
        file_type = detect_file_type(file_path)
        if file_type == "zip":
            with ZipFile(file_path) as zip_file:
                result = get_result_dataframe_from_compressed_file(zip_file, separator)
        elif file_type == "gzip":
            with GzipFile(file_path) as gzip_file:
                result = get_result_dataframe_from_compressed_file(gzip_file, separator)
        else:
            raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_BAD_ZIP)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.warning(f"Get dataframe from zip error: {e}", exc_info=True)
        delete_file(file_path)
        raise e
    return result


def get_result_dataframe_from_compressed_file(file: ZipFile | GzipFile, separator: str) -> DataFrame | None:
    result = None
    temp_path = ""

    try:
        if isinstance(file, ZipFile):
            name_list = file.namelist()
        elif isinstance(file, GzipFile):
            if file.read(10).startswith(b"<?xml"):
                name_list = ["file.xes"]
            else:
                name_list = ["file.csv"]
            file.seek(0)
        else:
            raise ValueError(ErrorType.EVENT_LOG_BAD_ZIP)

        filtered_name_list = [name for name in name_list if name not in path.EXCLUDED_EXTRACTED_FILE_NAMES]

        if len(filtered_name_list) != 1:
            raise HTTPException(status_code=400, detail="Zip file should contain only one file")

        filename = filtered_name_list[0]
        extension = get_extension(filename)

        if extension not in path.ALLOWED_EXTRACTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Zip file should contain only xes or csv file")

        temp_path = get_new_path(base_path=f"{path.TEMP_PATH}/", suffix=f".{extension}")

        with open(temp_path, "wb") as f:
            f.write(file.read(filename) if isinstance(file, ZipFile) else file.read())

        if extension == "xes":
            result = get_dataframe_from_xes(temp_path)
        elif extension == "csv":
            result = get_dataframe_from_csv(temp_path, separator)
    finally:
        delete_file(temp_path)

    return result


def detect_file_type(file_path: str) -> str:
    with open(file_path, "rb") as file:
        file_signature = file.read(2)
    if file_signature == b"\x50\x4b":  # PK (ZIP file signature)
        return "zip"
    elif file_signature == b"\x1f\x8b":  # 1F 8B (gzip file signature)
        return "gzip"
    return "unknown"
