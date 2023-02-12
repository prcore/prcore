import logging
from datetime import datetime
from threading import Event
from time import sleep

from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
from core.starters.database import SessionLocal
from core.enums.message import MessageType
from core.enums.status import PluginStatus, PluginStatusGroup, ProjectStatus
from core.functions.message.util import get_data_from_body
from core.starters import memory

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
