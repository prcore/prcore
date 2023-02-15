import logging
from datetime import datetime
from subprocess import run
from time import sleep
from typing import Any, Callable, List

from apscheduler.schedulers.background import BackgroundScheduler
from pandas import DataFrame, read_pickle, read_csv
from pika import BlockingConnection
from pika.exceptions import AMQPConnectionError
from pika.spec import BasicProperties
from tzlocal import get_localzone

from core import confs
from core.confs import config, path
from core.enums.definition import ColumnDefinition
from core.enums.message import MessageType
from core.functions.general.etc import get_message_id, get_readable_time
from core.functions.general.file import move_file
from core.functions.message.util import get_body, send_message
from core.starters.rabbitmq import parameters

# Enable logging
logger = logging.getLogger(__name__)


def plugin_run(basic_info: dict, callback: Callable, processed_messages_clean: Callable) -> None:
    connection = None
    try:
        # Start the scheduler
        scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 300}, timezone=str(get_localzone()))
        scheduler.add_job(log_rotation, "cron", hour=23, minute=59)
        scheduler.add_job(processed_messages_clean, "interval", minutes=5)
        scheduler.start()
        # Start the rabbitmq connection
        while True:
            try:
                connection = BlockingConnection(parameters)
                break
            except AMQPConnectionError:
                logger.warning("Connection to RabbitMQ failed. Trying again in 5 seconds...")
                sleep(5)
        logger.warning("Connection to RabbitMQ established")
        channel = connection.channel()
        channel.queue_declare(queue=config.APP_ID)
        channel.basic_consume(queue=config.APP_ID, on_message_callback=callback)
        channel.basic_publish(
            exchange="",
            routing_key="core",
            body=get_body(MessageType.ONLINE_REPORT, basic_info),
            properties=BasicProperties(message_id=get_message_id())
        )
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.warning("Plugin stopped by user")
    finally:
        connection and connection.close()


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


def get_error_data(instance: Any, detail: str) -> dict:
    return {
        "project_id": instance.get_project_id(),
        "plugin_id": instance.get_plugin_id(),
        "detail": detail
    }


def log_rotation() -> bool:
    # Log rotation
    result = False

    try:
        move_file(f"{confs.log_path}/log", f"{confs.log_path}/log-{get_readable_time(the_format='%Y%m%d')}")

        with open(f"{confs.log_path}/log", "w", encoding="utf-8") as f:
            f.write("")

        # Reconfigure the logger
        [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.WARNING,
            filename=f"{confs.log_path}/log",
            filemode="a"
        )

        run(f"find {confs.log_path}/log-* -mtime +30 -delete", shell=True)

        result = True
    except Exception as e:
        logger.warning(f"Log rotation error: {e}", exc_info=True)

    return result
