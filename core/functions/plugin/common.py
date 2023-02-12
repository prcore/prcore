import logging
from datetime import datetime
from typing import Any, Callable, List

from pandas import DataFrame, read_pickle
from pika import BlockingConnection

from core.confs import config, path
from core.enums.definition import ColumnDefinition
from core.enums.message import MessageType
from core.functions.message.util import get_body, send_message
from core.starters.rabbitmq import parameters

# Enable logging
logger = logging.getLogger(__name__)


def plugin_run(basic_info: dict, callback: Callable):
    connection = None
    try:
        connection = BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=config.APP_ID)
        channel.basic_consume(queue=config.APP_ID, on_message_callback=callback)
        channel.basic_publish(exchange="", routing_key="core", body=get_body(MessageType.ONLINE_REPORT, basic_info))
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.warning("Plugin stopped by user")
    finally:
        connection and connection.close()


def read_training_df(training_df_name: str) -> DataFrame:
    return read_pickle(f"{path.EVENT_LOG_TRAINING_DF_PATH}/{training_df_name}")


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


def get_null_output(plugin_name: str, plugin_type: str, detail: str) -> dict:
    return {
        "date": datetime.now(),
        "type": plugin_type,
        "outcome": None,
        "model": {
            "name": plugin_name,
            "detail": detail
        }
    }


def start_training(project_id: int, instance: Any) -> None:
    preprocess_result = instance.preprocess()
    if not preprocess_result:
        send_message("core", MessageType.ERROR_REPORT, {"project_id": project_id, "detail": "Pre-process failed"})
    else:
        send_message("core", MessageType.TRAINING_START, {"project_id": project_id})
    train_result = instance.train()
    if not train_result:
        send_message("core", MessageType.ERROR_REPORT, {"project_id": project_id, "detail": "Train failed"})
    model_name = instance.save_model()
    if not model_name:
        send_message("core", MessageType.ERROR_REPORT, {"project_id": project_id, "detail": "Save model failed"})
    else:
        send_message("core", MessageType.MODEL_NAME, {"project_id": project_id, "model_name": model_name})
