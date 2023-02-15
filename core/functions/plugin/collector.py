import logging
from datetime import datetime

from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def get_active_plugins() -> dict:
    # Get all active plugins
    active_plugins = {}
    for plugin_key, plugin in memory.available_plugins.items():
        if is_plugin_active(plugin_key):
            active_plugins[plugin_key] = plugin
    return active_plugins


def is_plugin_active(plugin_key: str) -> bool:
    # Check if a plugin is active
    since_last_online = datetime.now() - memory.available_plugins.get(plugin_key, {"online": datetime.now()})["online"]
    return since_last_online.total_seconds() < 15 * 60
