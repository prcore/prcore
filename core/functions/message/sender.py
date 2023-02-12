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


def send_training_data_to_all_plugins(project_id: int, training_df_name: str, plugins: dict[str, int]) -> bool:
    # Send training data to all plugins
    return all(send_training_data(plugin_key, project_id, plugins[plugin_key], training_df_name)
               for plugin_key in plugins)


def send_training_data(plugin_key: str, project_id: int, plugin_id: int, training_df_name: str) -> bool:
    # Send training data to a specific plugin
    return send_message(plugin_key, MessageType.TRAINING_DATA, {
        "project_id": project_id,
        "plugin_id": plugin_id,
        "training_df_name": training_df_name
    })
