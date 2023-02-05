import datetime
import logging
from typing import Union

from pandas import read_pickle, DataFrame
from sqlalchemy.orm import Session

from core import confs, glovar
from core.crud.event_log import set_df_name
from core.models.event_log import EventLog
from core.functions.general.etc import get_current_time_label
from core.functions.general.file import get_new_path

# Enable logging
logger = logging.getLogger(__name__)

def get_dataframe(db_event_log: EventLog) -> DataFrame | None:
    # Get dataframe from memory or pickle file
    df = get_dataframe_from_memory(event_log_id=db_event_log.id)
    if df is None and db_event_log.df_name:
        df = get_dataframe_from_pickle(filename=db_event_log.df_name)
        save_dataframe_to_memory(event_log_id=db_event_log.id, df=df)
    return df


def get_dataframe_from_memory(event_log_id: int) -> DataFrame | None:
    # Get dataframe from memory
    return glovar.dataframes.get(event_log_id)


def get_dataframe_from_pickle(filename: str) -> DataFrame:
    # Get dataframe from pickle file
    return read_pickle(f"{confs.EVENT_LOG_DATAFRAME_PATH}/{filename}")


def save_dataframe(db: Session, db_event_log: EventLog, df: DataFrame) -> None:
    # Save dataframe to memory and pickle file
    save_dataframe_to_memory(event_log_id=db_event_log.id, df=df)
    dataframe_path = get_new_path(
        base_path=f"{confs.EVENT_LOG_DATAFRAME_PATH}/",
        prefix=f"{get_current_time_label()}-",
        suffix=".pkl"
    )
    set_df_name(db, db_event_log, dataframe_path.split("/")[-1])
    save_dataframe_to_pickle(path=dataframe_path, df=df)


def save_dataframe_to_memory(event_log_id: int, df: DataFrame) -> None:
    # Save dataframe to memory
    glovar.dataframes[event_log_id] = df


def save_dataframe_to_pickle(path: str, df: DataFrame) -> None:
    # Save dataframe to pickle file
    df.to_pickle(path)