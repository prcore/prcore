import logging
from datetime import datetime

from core.confs import config
from core.enums.message import MessageType
from core.starters import memory
from core.functions.message.util import send_message

# Enable logging
logger = logging.getLogger(__name__)


def send_online_inquires() -> bool:
    # Send online inquiries to all plugins
    return all(send_online_inquiry(plugin_id) for plugin_id in config.ENABLED_PLUGINS)


def send_online_inquiry(plugin_id: str) -> bool:
    # Send online inquiry to a specific plugin
    return send_message(plugin_id, MessageType.ONLINE_INQUIRY, {})


def send_training_data_to_all_plugins(project_id: int, training_data_name: str) -> bool:
    # Send training data to all plugins
    return all(send_training_data(plugin_id, project_id, training_data_name) for plugin_id in get_active_plugins())


def send_training_data(plugin_id: str, project_id: int, training_data_name: str) -> bool:
    # Send training data to a specific plugin
    return send_message(plugin_id, MessageType.TRAINING_DATA, {
        "project_id": project_id,
        "training_data_name": training_data_name
    })


def get_active_plugins() -> list[str]:
    # Get all active plugins
    return [plugin_id for plugin_id in list(memory.available_plugins) if is_plugin_active(plugin_id)]


def is_plugin_active(plugin_id: str) -> bool:
    # Check if a plugin is active
    since_last_online = datetime.now() - memory.available_plugins.get(plugin_id, {"online": datetime.now()})["online"]
    return since_last_online.total_seconds() < 15 * 60
