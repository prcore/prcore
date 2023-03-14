import logging
from typing import Any

# Enable logging
logger = logging.getLogger(__name__)


def get_parameters_for_plugin(plugin_key: str, active_plugins: dict, parameters: dict[str, Any]) -> dict[str, Any]:
    default_params = active_plugins.get(plugin_key, {}).get("parameters", {})
    plugin_params = parameters.get(plugin_key, {})
    return {**default_params, **plugin_params}
