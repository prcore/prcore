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


def send_training_data_to_all_plugins(project_id: int, training_df_name: str, plugin_ids: list[str]) -> bool:
    # Send training data to all plugins
    return all(send_training_data(plugin_id, project_id, training_df_name) for plugin_id in plugin_ids)


def send_training_data(plugin_id: str, project_id: int, training_df_name: str) -> bool:
    # Send training data to a specific plugin
    return send_message(plugin_id, MessageType.TRAINING_DATA, {
        "project_id": project_id,
        "training_df_name": training_df_name
    })
