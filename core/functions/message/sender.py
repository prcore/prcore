import logging
from datetime import datetime
from typing import Any

import core.schemas.definition as definition_schema
from core.confs import config
from core.enums.message import MessageType
from core.functions.common.etc import random_str
from core.functions.message.util import send_message
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def send_online_inquires() -> bool:
    # Send online inquiries to all plugins
    result = False

    try:
        result = all(send_online_inquiry(plugin_id) for plugin_id in config.ENABLED_PLUGINS)
    except Exception as e:
        logger.warning(f"Send online inquiries error: {e}", exc_info=True)

    return result


def send_online_inquiry(plugin_id: str) -> bool:
    # Send online inquiry to a specific plugin
    return send_message(plugin_id, MessageType.ONLINE_INQUIRY, {})


def send_training_data_to_all_plugins(plugins: dict[str, int], project_id: int, training_df_name: str,
                                      parameters: dict[str, dict[str, Any]],
                                      additional_infos: dict[str, dict[str, Any]]) -> bool:
    # Send training data to all plugins
    return all(send_training_data(plugin_key, project_id, plugins[plugin_key], training_df_name,
                                  parameters.get(plugin_key, {}), additional_infos.get(plugin_key, {}))
               for plugin_key in plugins)


def send_training_data(plugin_key: str, project_id: int, plugin_id: int, training_df_name: str,
                       parameters: dict[str, Any], additional_info: dict[str, Any]) -> bool:
    # Send training data to a specific plugin
    return send_message(plugin_key, MessageType.TRAINING_DATA, {
        "project_id": project_id,
        "plugin_id": plugin_id,
        "training_df_name": training_df_name,
        "parameters": parameters,
        "additional_info": additional_info
    })


def send_dataset_prescription_request_to_all_plugins(plugins: dict[str, int], project_id: int,
                                                     model_names: dict[int, str], result_key: str, dataset_name: str,
                                                     additional_infos: dict[str, dict[str, Any]]) -> bool:
    # Send ongoing dataset to all plugins
    return all(send_dataset_prescription_request(plugin_key, project_id, model_names[plugins[plugin_key]], result_key,
                                                 dataset_name, additional_infos.get(plugin_key, {}))
               for plugin_key in plugins)


def send_dataset_prescription_request(plugin_key: str, project_id: int, model_name: str, result_key: str,
                                      ongoing_df_name: str, additional_info: dict[str, Any]) -> bool:
    # Send ongoing dataset to a specific plugin
    return send_message(plugin_key, MessageType.DATASET_PRESCRIPTION_REQUEST, {
        "project_id": project_id,
        "model_name": model_name,
        "result_key": result_key,
        "ongoing_df_name": ongoing_df_name,
        "additional_info": additional_info
    })


def send_streaming_prepare_to_all_plugins(plugins: dict[str, int], project_id: int, model_names: dict[int, str],
                                          additional_infos: dict[str, dict[str, Any]]) -> bool:
    # Send streaming prepare to all plugins
    return all(send_streaming_prepare(plugin_key, project_id, model_names[plugins[plugin_key]],
                                      additional_infos.get(plugin_key, {}))
               for plugin_key in plugins)


def send_streaming_prepare(plugin_key: str, project_id: int, model_name: str, additional_info: dict[str, Any]) -> bool:
    # Send streaming prepare to a specific plugin
    return send_message(plugin_key, MessageType.STREAMING_PREPARE, {
        "project_id": project_id,
        "model_name": model_name,
        "additional_info": additional_info
    })


def send_streaming_prescription_request_to_all_plugins(plugins: list[str], project_id: int, model_names: dict[str, str],
                                                       event_id: int, prefix: list[dict],
                                                       additional_infos: dict[str, dict[str, Any]]) -> bool:
    # Send prescription request to all plugins
    return all(send_streaming_prescription_request(plugin_key, project_id, model_names[plugin_key], event_id, prefix,
                                                   additional_infos.get(plugin_key, {}))
               for plugin_key in plugins)


def send_streaming_prescription_request(plugin_key: str, project_id: int, model_name: str, event_id: int,
                                        prefix: list[dict], additional_info: dict[str, Any]) -> bool:
    # Send prescription request to a specific plugin
    return send_message(plugin_key, MessageType.STREAMING_PRESCRIPTION_REQUEST, {
        "project_id": project_id,
        "model_name": model_name,
        "event_id": event_id,
        "data": prefix,
        "additional_info": additional_info
    })


def send_streaming_stop_to_all_plugins(plugins: list[str], project_id: int) -> bool:
    # Send streaming stop to all plugins
    return all(send_streaming_stop(plugin_key, project_id) for plugin_key in plugins)


def send_streaming_stop(plugin_key: str, project_id: int) -> bool:
    # Send streaming stop to a specific plugin
    return send_message(plugin_key, MessageType.STREAMING_STOP, {
        "project_id": project_id
    })


def send_process_request(df_name: str, definition: definition_schema.Definition) -> str:
    # Send process request to the data processor
    request_key = random_str(8)
    while request_key in list(memory.pending_dfs):
        request_key = random_str(8)
    memory.pending_dfs[request_key] = {
        "date": datetime.now(),
        "df_name": df_name,
        "finished": False
    }
    definition = definition.dict()
    for key, value in definition.items():
        if isinstance(value, datetime):
            definition[key] = value.isoformat()
    send_message(
        receiver_id="processor",
        message_type=MessageType.PROCESS_REQUEST,
        data={
            "request_key": request_key,
            "df_name": df_name,
            "definition": definition
        }
    )
    return request_key
