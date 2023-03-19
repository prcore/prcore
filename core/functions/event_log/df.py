import logging
from zipfile import BadZipFile

from fastapi import HTTPException, UploadFile
from pandas import DataFrame
from sqlalchemy.orm import Session

from core.confs import path
from core.crud.event_log import set_df_name
from core.enums.error import ErrorType
from core.functions.common.etc import get_current_time_label
from core.functions.common.file import get_new_path, get_dataframe_from_pickle, save_dataframe_to_pickle
from core.functions.event_log.file import get_dataframe_from_file
from core.models.event_log import EventLog
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe(db_event_log: EventLog) -> DataFrame | None:
    # Get dataframe from memory or pickle file
    return get_dataframe_by_id_or_name(event_log_id=db_event_log.id, df_name=db_event_log.df_name)


def get_dataframe_by_id_or_name(event_log_id: int, df_name: str) -> DataFrame | None:
    # Get dataframe from memory or pickle file
    df = get_dataframe_from_memory(event_log_id=event_log_id)
    if df is None and df_name:
        df = get_dataframe_from_pickle(f"{path.EVENT_LOG_DATAFRAME_PATH}/{df_name}")
        save_dataframe_to_memory(event_log_id=event_log_id, df=df)
    return df


def get_dataframe_from_memory(event_log_id: int) -> DataFrame | None:
    # Get dataframe from memory
    return memory.dataframes.get(event_log_id)


def get_df_from_uploaded_file(file: UploadFile, extension: str, separator: str) -> tuple[DataFrame, str]:
    # Save the file
    raw_path = get_new_path(
        base_path=f"{path.EVENT_LOG_RAW_PATH}/",
        prefix=f"{get_current_time_label()}-",
        suffix=f".{extension}"
    )

    with open(raw_path, "wb") as f:
        f.write(file.file.read())

    # Get dataframe from file
    try:
        df = get_dataframe_from_file(raw_path, extension, separator)
    except BadZipFile:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_BAD_ZIP)
    except Exception as e:
        logger.warning(f"Failed to get dataframe from file {raw_path}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    return df, raw_path


def save_dataframe(db: Session, db_event_log: EventLog, df: DataFrame) -> None:
    # Save dataframe to memory and pickle file
    save_dataframe_to_memory(event_log_id=db_event_log.id, df=df)
    dataframe_path = get_new_path(
        base_path=f"{path.EVENT_LOG_DATAFRAME_PATH}/",
        prefix=f"{get_current_time_label()}-",
        suffix=".pkl"
    )
    set_df_name(db, db_event_log, dataframe_path.split("/")[-1])
    save_dataframe_to_pickle(df_path=dataframe_path, df=df)


def save_dataframe_to_memory(event_log_id: int, df: DataFrame) -> None:
    # Save dataframe to memory
    memory.dataframes[event_log_id] = df
