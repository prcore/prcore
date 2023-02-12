import logging
from datetime import datetime
from typing import Callable, List

from pandas import DataFrame, read_pickle
from pika import BlockingConnection

from core.confs import config, path
from core.enums.definition import ColumnDefinition
from core.enums.message import MessageType
from core.functions.message.util import get_body
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
