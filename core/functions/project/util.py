import logging

from core.enums.status import PluginStatus, PluginStatusGroup, ProjectStatus

# Enable logging
logger = logging.getLogger(__name__)


def get_project_status(plugin_statuses: list[PluginStatus | str]) -> ProjectStatus | str | None:
    # Get the status of the project based on the statuses of the plugins
    if all(plugin_status in PluginStatusGroup.STREAMING for plugin_status in plugin_statuses):
        return ProjectStatus.STREAMING
    elif all(plugin_status in PluginStatusGroup.ACTIVATING for plugin_status in plugin_statuses):
        return ProjectStatus.ACTIVATING
    elif all(plugin_status in PluginStatusGroup.TRAINED for plugin_status in plugin_statuses):
        return ProjectStatus.TRAINED
    elif all(plugin_status in PluginStatusGroup.TRAINING for plugin_status in plugin_statuses):
        return ProjectStatus.TRAINING
    elif all(plugin_status in PluginStatusGroup.PREPROCESSING for plugin_status in plugin_statuses):
        return ProjectStatus.PREPROCESSING
    elif all(plugin_status in PluginStatusGroup.WAITING for plugin_status in plugin_statuses):
        return ProjectStatus.WAITING
    elif any(plugin_status in PluginStatusGroup.WAITING for plugin_status in plugin_statuses):
        return get_project_status([plugin_status for plugin_status in plugin_statuses
                                   if plugin_status in PluginStatusGroup.WAITING])
    else:
        return "Plugins encountered errors"
