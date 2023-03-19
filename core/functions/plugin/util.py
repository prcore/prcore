import logging
from datetime import datetime
from typing import Any

from core.schemas import definition as definition_schema
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def get_parameters_for_plugin(plugin_key: str, active_plugins: dict, parameters: dict[str, Any]) -> dict[str, Any]:
    default_params = active_plugins.get(plugin_key, {}).get("parameters", {})
    plugin_params = parameters.get(plugin_key, {})
    return {**default_params, **plugin_params}


def enhance_additional_infos(additional_infos: dict[str, dict[str, Any]], active_plugins: dict[str, dict[str, Any]],
                             definition: definition_schema.Definition) -> dict[str, dict[str, Any]]:
    # Enhance additional infos
    definition = definition.dict()
    for plugin_key, plugin_info in active_plugins.items():
        additional_infos[plugin_key] = enhance_additional_info(additional_infos.get(plugin_key, {}), plugin_info,
                                                               definition)
    return additional_infos


def enhance_additional_info(additional_info: dict[str, Any], plugin_info: dict[str, Any],
                            definition: dict[str, Any]) -> dict[str, Any]:
    # Enhance additional info from the definition
    needed_info_for_training = plugin_info.get("needed_info_for_training", [])
    needed_info_for_prediction = plugin_info.get("needed_info_for_prediction", [])
    needed_info = needed_info_for_training + needed_info_for_prediction
    for info in needed_info:
        if info in definition:
            additional_info[info] = definition[info]
    return additional_info


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
