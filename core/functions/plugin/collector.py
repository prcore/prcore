import logging
from datetime import datetime

from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def get_active_plugins() -> list[str]:
    # Get all active plugins
    return [plugin_id for plugin_id in list(memory.available_plugins) if is_plugin_active(plugin_id)]


def is_plugin_active(plugin_id: str) -> bool:
    # Check if a plugin is active
    since_last_online = datetime.now() - memory.available_plugins.get(plugin_id, {"online": datetime.now()})["online"]
    return since_last_online.total_seconds() < 15 * 60
