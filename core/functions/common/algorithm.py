from datetime import datetime
from typing import List, Any

from pandas import DataFrame, read_pickle, read_csv

from core.confs import path
from core.enums.definition import ColumnDefinition
from core.enums.message import MessageType
from core.functions.message.util import send_message


def read_training_df(training_df_name: str) -> DataFrame:
    try:
        return read_pickle(f"{path.EVENT_LOG_TRAINING_DF_PATH}/{training_df_name}")
    except ValueError:
        training_csv_name = training_df_name.replace(".pkl", ".csv")
        return read_csv(f"{path.EVENT_LOG_TRAINING_DF_PATH}/{training_csv_name}")


def check_training_df(df: DataFrame, needed_columns: List[str]) -> bool:
    if ColumnDefinition.CASE_ID not in df.columns:
        return False
    if not get_timestamp_columns(df):
        return False
    if ColumnDefinition.ACTIVITY not in df.columns:
        return False
    for column in needed_columns:
        if column in {ColumnDefinition.CASE_ID,
                      ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP,
                      ColumnDefinition.ACTIVITY}:
            continue
        if column not in df.columns:
            return False
    return True


def get_timestamp_columns(df: DataFrame) -> List[str]:
    if ColumnDefinition.TIMESTAMP in df.columns:
        return [ColumnDefinition.TIMESTAMP]
    elif ColumnDefinition.START_TIMESTAMP in df.columns and ColumnDefinition.END_TIMESTAMP in df.columns:
        return [ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP]
    else:
        return []


def start_training(instance: Any) -> None:
    preprocess_result = instance.preprocess()
    if not preprocess_result:
        send_message("core", MessageType.ERROR_REPORT, get_error_data(instance, "Pre-process failed"))
    else:
        send_message(
            receiver_id="core",
            message_type=MessageType.TRAINING_START,
            data={
                "project_id": instance.get_project_id(),
                "plugin_id": instance.get_plugin_id()
            }
        )
    train_result = instance.train()
    if not train_result:
        send_message("core", MessageType.ERROR_REPORT, get_error_data(instance, "Train failed"))
    model_name = instance.save_model()
    if not model_name:
        send_message("core", MessageType.ERROR_REPORT, get_error_data(instance, "Save model failed"))
    else:
        send_message(
            receiver_id="core",
            message_type=MessageType.MODEL_NAME,
            data={
                "project_id": instance.get_project_id(),
                "plugin_id": instance.get_plugin_id(),
                "model_name": model_name
            }
        )


def get_null_output(plugin_name: str, plugin_type: str, detail: str) -> dict:
    return {
        "date": datetime.now().isoformat(),
        "type": plugin_type,
        "output": None,
        "model": {
            "name": plugin_name,
            "detail": detail
        }
    }


def get_error_data(instance: Any, detail: str) -> dict:
    return {
        "project_id": instance.get_project_id(),
        "plugin_id": instance.get_plugin_id(),
        "detail": detail
    }
