import logging
from datetime import datetime

from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def get_active_plugins() -> dict:
    # Get all active plugins
    active_plugins = {}
    for plugin_id, plugin in memory.available_plugins.items():
        if is_plugin_active(plugin_id):
            active_plugins[plugin_id] = plugin
    return active_plugins


def is_plugin_active(plugin_id: str) -> bool:
    # Check if a plugin is active
    since_last_online = datetime.now() - memory.available_plugins.get(plugin_id, {"online": datetime.now()})["online"]
    return since_last_online.total_seconds() < 15 * 60
