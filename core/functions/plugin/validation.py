import logging

from fastapi import HTTPException

import core.models.plugin as plugin_model
from core.enums.error import ErrorType
from core.enums.status import PluginStatus

# Enable logging
logger = logging.getLogger(__name__)


def validation_plugin_status(db_plugin: plugin_model.Plugin) -> None:
    if not db_plugin:
        raise HTTPException(status_code=404, detail=ErrorType.PLUGIN_NOT_FOUND)
    if db_plugin.status != PluginStatus.TRAINED:
        raise HTTPException(status_code=400, detail=ErrorType.PLUGIN_NOT_READY)
