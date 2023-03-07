import logging
from datetime import datetime
from typing import Any, Dict, List, Type

from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

from core.confs import config, path
from core.enums.definition import ColumnDefinition
from core.enums.message import MessageType
from core.functions.message.util import send_message_by_channel, get_data_from_body

from plugins.common import memory
from plugins.common.algorithm import Algorithm, read_df_from_path, check_training_df
from plugins.common.initializer import (preprocess_and_train, activate_instance_from_model_file,
                                        get_instance_from_model_file, deactivate_instance)

# Enable logging
logger = logging.getLogger(__name__)


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes,
             basic_info: Dict[str, Any], needed_columns: List[ColumnDefinition], algo: Type[Algorithm]) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, properties.message_id, data)
    print("-" * 24)

    try:
        message_id = properties.message_id
        if memory.processed_messages.get(message_id):
            return
        else:
            memory.processed_messages[message_id] = datetime.now()
        if message_type == MessageType.ONLINE_INQUIRY:
            handle_online_inquiry(ch, basic_info)
        elif message_type == MessageType.TRAINING_DATA:
            handle_training_data(ch, data, algo, basic_info, needed_columns)
        elif message_type == MessageType.DATASET_PRESCRIPTION_REQUEST:
            instance = get_instance_from_model_file(algo, basic_info, data["project_id"], data["model_name"])
            handle_dataset_prescription_request(ch, data, instance)
        elif message_type == MessageType.STREAMING_PREPARE:
            handle_streaming_prepare(ch, data, algo, basic_info)
        elif message_type == MessageType.STREAMING_PRESCRIPTION_REQUEST:
            instance = get_instance_from_model_file(algo, basic_info, data["project_id"], data["model_name"])
            handle_streaming_prescription_request(ch, data, instance)
        elif message_type == MessageType.STREAMING_STOP:
            deactivate_instance(data["project_id"])
    except Exception as e:
        logger.warning(f"Callback error: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def handle_online_inquiry(ch: BlockingChannel, basic_info: dict) -> None:
    send_message_by_channel(ch, "core", MessageType.ONLINE_REPORT, basic_info)


def handle_training_data(ch: BlockingChannel, data: dict, algo: Type[Algorithm], basic_info: Dict[str, Any],
                         needed_columns: list) -> bool:
    result = False
    project_id = None
    plugin_id = None

    try:
        project_id = data["project_id"]
        plugin_id = data["plugin_id"]
        training_df_name = data["training_df_name"]
        treatment_definition = data["treatment_definition"]
        training_df = read_df_from_path(path.EVENT_LOG_TRAINING_DF_PATH, training_df_name)
        applicable = check_training_df(training_df, needed_columns)
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.DATA_REPORT,
            data={"project_id": project_id, "plugin_id": plugin_id, "applicable": applicable}
        )
        if not applicable:
            return False
        preprocess_and_train(algo, basic_info, project_id, plugin_id, training_df, treatment_definition)
        result = True
    except Exception as e:
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.ERROR_REPORT,
            data={"project_id": project_id, "plugin_id": plugin_id, "detail": "Error while processing data"}
        )
        logger.warning(f"Handle training data failed: {e}", exc_info=True)

    return result


def handle_dataset_prescription_request(ch: BlockingChannel, data: dict, instance: Algorithm) -> None:
    project_id = data["project_id"]
    result_key = data["result_key"]
    ongoing_df_name = data["ongoing_df_name"]
    df = read_df_from_path(path.TEMP_PATH, ongoing_df_name)
    result = instance.predict_df(df)
    send_message_by_channel(
        channel=ch,
        receiver_id="core",
        message_type=MessageType.DATASET_PRESCRIPTION_RESULT,
        data={"project_id": project_id, "plugin_key": config.APP_ID, "result_key": result_key, "data": result}
    )
    deactivate_instance(project_id)


def handle_streaming_prepare(ch: BlockingChannel, data: dict, algo: Type[Algorithm],
                             basic_info: Dict[str, Any]) -> None:
    project_id = data["project_id"]
    model_name = data["model_name"]
    plugin_ud = activate_instance_from_model_file(algo, basic_info, project_id, model_name)
    if plugin_ud:
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.STREAMING_READY,
            data={"project_id": project_id, "plugin_id": plugin_ud}
        )


def handle_streaming_prescription_request(ch: BlockingChannel, data: dict, instance: Algorithm) -> None:
    project_id = data["project_id"]
    event_id = data["event_id"]
    prefix = data["data"]
    result = instance.predict(prefix)
    send_message_by_channel(
        channel=ch,
        receiver_id="core",
        message_type=MessageType.STREAMING_PRESCRIPTION_RESULT,
        data={"project_id": project_id, "plugin_key": config.APP_ID, "event_id": event_id, "data": result}
    )
