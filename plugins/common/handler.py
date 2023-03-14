import logging
from datetime import datetime
from typing import Any, Dict, Type

from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

from core.confs import path
from core.enums.message import MessageType
from core.functions.message.util import get_data_from_body

from plugins.common import memory
from plugins.common.algorithm import Algorithm, get_null_output
from plugins.common.check import check_needed_columns, check_column_classes, check_needed_info
from plugins.common.dataset import read_df_from_path
from plugins.common.initializer import (preprocess_and_train, activate_instance_from_model_file,
                                        get_instance_from_model_file, deactivate_instance)
from plugins.common.sender import (send_online_report, send_data_report, send_error_report,
                                   send_dataset_prescription_result, send_streaming_ready,
                                   send_streaming_prescription_result)

# Enable logging
logger = logging.getLogger(__name__)


def callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties, body: bytes,
        algo: Type[Algorithm],
        basic_info: Dict[str, Any]
) -> None:
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
            handle_online_inquiry(basic_info)
        elif message_type == MessageType.TRAINING_DATA:
            handle_training_data(ch, data, algo, basic_info)
        elif message_type == MessageType.DATASET_PRESCRIPTION_REQUEST:
            handle_dataset_prescription_request(ch, data, algo, basic_info)
        elif message_type == MessageType.STREAMING_PREPARE:
            handle_streaming_prepare(ch, data, algo, basic_info)
        elif message_type == MessageType.STREAMING_PRESCRIPTION_REQUEST:
            handle_streaming_prescription_request(ch, data, algo, basic_info)
        elif message_type == MessageType.STREAMING_STOP:
            deactivate_instance(data["project_id"])
    except Exception as e:
        logger.warning(f"Callback error: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def handle_online_inquiry(basic_info: dict) -> None:
    send_online_report(basic_info)


def handle_training_data(ch: BlockingChannel, data: Dict[str, Any], algo: Type[Algorithm],
                         basic_info: Dict[str, Any]) -> bool:
    result = False
    project_id = None
    plugin_id = None

    try:
        project_id = data["project_id"]
        plugin_id = data["plugin_id"]
        training_df_name = data["training_df_name"]
        additional_info = data["additional_info"]
        training_df = read_df_from_path(path.EVENT_LOG_TRAINING_DF_PATH, training_df_name)

        needed_columns = basic_info.get("needed_columns", [])
        needed_info_for_training = basic_info.get("needed_info_for_training", [])
        columns_check = check_needed_columns(training_df, needed_columns)
        if not columns_check:
            return send_data_report(ch, project_id, plugin_id, columns_check)
        classes_check_error = check_column_classes(training_df, needed_columns)
        if classes_check_error:
            return send_error_report(project_id, plugin_id, classes_check_error)
        info_check = check_needed_info(additional_info, needed_info_for_training)
        if not info_check:
            return send_data_report(ch, project_id, plugin_id, info_check)

        default_params = basic_info.get("parameters", {})
        user_params = data.get("parameters", {})
        parameters = {**default_params, **user_params}
        algo_data = {
            "basic_info": basic_info,
            "project_id": project_id,
            "plugin_id": plugin_id,
            "df": training_df,
            "parameters": parameters,
            "additional_info": additional_info
        }
        preprocess_and_train(algo, algo_data)
        result = True
    except Exception as e:
        send_error_report(project_id, plugin_id, f"Error while pre-processing data: {e}")
        logger.warning(f"Handle training data failed: {e}", exc_info=True)

    return result


def handle_dataset_prescription_request(ch: BlockingChannel, data: dict, algo: Type[Algorithm],
                                        basic_info: Dict[str, Any]) -> None:
    project_id = data["project_id"]
    model_name = data["model_name"]
    result_key = data["result_key"]
    ongoing_df_name = data["ongoing_df_name"]
    additional_info = data["additional_info"]
    instance = get_instance_from_model_file(algo, {
        "project_id": project_id,
        "model_name": model_name,
        "basic_info": basic_info,
        "additional_info": additional_info
    })
    df = read_df_from_path(path.TEMP_PATH, ongoing_df_name)
    try:
        result = instance.predict_df(df)
    except Exception as e:
        logger.warning(f"Predicting df failed: {e}", exc_info=True)
        result = {}
    send_dataset_prescription_result(ch, project_id, result_key, result)
    deactivate_instance(project_id)


def handle_streaming_prepare(ch: BlockingChannel, data: dict, algo: Type[Algorithm],
                             basic_info: Dict[str, Any]) -> None:
    project_id = data["project_id"]
    model_name = data["model_name"]
    plugin_id = activate_instance_from_model_file(
        algo=algo,
        algo_data={
            "basic_info": basic_info,
            "project_id": project_id,
            "model_name": model_name
        }
    )
    if not plugin_id:
        send_error_report(project_id, plugin_id, "Error while activating instance")
        return
    send_streaming_ready(ch, project_id, plugin_id)


def handle_streaming_prescription_request(ch: BlockingChannel, data: dict, algo: Type[Algorithm],
                                          basic_info: Dict[str, Any]) -> None:
    project_id = data["project_id"]
    model_name = data["model_name"]
    event_id = data["event_id"]
    prefix = data["data"]
    additional_info = data["additional_info"]
    instance = get_instance_from_model_file(algo, {
        "project_id": project_id,
        "model_name": model_name,
        "basic_info": basic_info,
        "additional_info": additional_info
    })
    try:
        result = instance.predict(prefix)
    except Exception as e:
        logger.warning(f"Predicting prefix failed: {e}", exc_info=True)
        result = get_null_output(instance, f"Predicting prefix failed： {e}")

    send_streaming_prescription_result(ch, project_id, event_id, result)
