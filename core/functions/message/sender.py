import logging

from core.confs import config
from core.enums.message import MessageType
from core.functions.message.util import send_message

# Enable logging
logger = logging.getLogger(__name__)


def send_online_inquires() -> bool:
    # Send online inquiries to all plugins
    return all(send_online_inquiry(plugin_id) for plugin_id in config.ENABLED_PLUGINS)


def send_online_inquiry(plugin_id: str) -> bool:
    # Send online inquiry to a specific plugin
    return send_message(plugin_id, MessageType.ONLINE_INQUIRY, {})


def send_training_data_to_all_plugins(project_id: int, training_df_name: str, treatment_definition: list,
                                      plugins: dict[str, int]) -> bool:
    # Send training data to all plugins
    return all(send_training_data(plugin_key, project_id, plugins[plugin_key], training_df_name, treatment_definition)
               for plugin_key in plugins)


def send_training_data(plugin_key: str, project_id: int, plugin_id: int, training_df_name: str,
                       treatment_definition: list) -> bool:
    # Send training data to a specific plugin
    return send_message(plugin_key, MessageType.TRAINING_DATA, {
        "project_id": project_id,
        "plugin_id": plugin_id,
        "training_df_name": training_df_name,
        "treatment_definition": treatment_definition
    })


def send_streaming_prepare_to_all_plugins(project_id: int, plugins: dict[str, int],
                                          model_names: dict[int, str]) -> bool:
    # Send streaming prepare to all plugins
    return all(send_streaming_prepare(plugin_key, project_id, model_names[plugins[plugin_key]])
               for plugin_key in plugins)


def send_streaming_prepare(plugin_key: str, project_id: int, model_name: str) -> bool:
    # Send streaming prepare to a specific plugin
    return send_message(plugin_key, MessageType.STREAMING_PREPARE, {
        "project_id": project_id,
        "model_name": model_name
    })


def send_prescription_request_to_all_plugins(project_id: int, plugins: list[str], model_names: dict[str, str],
                                             event_id: int, prefix: list[dict]) -> bool:
    # Send prescription request to all plugins
    return all(send_prescription_request(plugin_key, project_id, model_names[plugin_key], event_id, prefix)
               for plugin_key in plugins)


def send_prescription_request(plugin_key: str, project_id: int, model_name: str, event_id: int,
                              prefix: list[dict]) -> bool:
    # Send prescription request to a specific plugin
    return send_message(plugin_key, MessageType.PRESCRIPTION_REQUEST, {
        "project_id": project_id,
        "model_name": model_name,
        "event_id": event_id,
        "data": prefix
    })


def send_streaming_stop_to_all_plugins(project_id: int, plugins: list[str]) -> bool:
    # Send streaming stop to all plugins
    return all(send_streaming_stop(plugin_key, project_id) for plugin_key in plugins)


def send_streaming_stop(plugin_key: str, project_id: int) -> bool:
    # Send streaming stop to a specific plugin
    return send_message(plugin_key, MessageType.STREAMING_STOP, {
        "project_id": project_id
    })
