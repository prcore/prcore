import logging

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

import core.crud.plugin as plugin_crud
import core.schemas.request.plugin as plugin_request
from core.enums.error import ErrorType
from core.functions.common.request import get_db
from core.functions.plugin.job import retrain_plugin
from core.functions.plugin.util import get_active_plugins
from core.functions.plugin.validation import validation_plugin_status
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def process_plugins_reading(skip: int, limit: int, db: Session) -> dict:
    return {
        "message": "Plugins retrieved successfully",
        "plugins": plugin_crud.get_plugins(db, skip=skip, limit=limit)
    }


def process_plugin_reading(plugin_id: int, db: Session) -> dict:
    db_plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
    if not db_plugin:
        raise HTTPException(status_code=404, detail=ErrorType.PLUGIN_NOT_FOUND)
    return {
        "message": "Plugin retrieved successfully",
        "plugin": db_plugin
    }


def process_available_plugins_reading() -> dict:
    return {
        "message": "Available plugins retrieved successfully",
        "plugins": get_active_plugins()
    }


def process_plugin_update(plugin_id: int, update_body: plugin_request.UpdatePluginRequest,
                          db: Session = Depends(get_db)) -> dict:
    db_plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
    db_project = validation_plugin_status(db, db_plugin)

    # Check if the plugin is needed to be retrained
    if (update_body.parameters
            or any(param in memory.available_plugins.get(db_plugin.key, {}).get("needed_info_for_training", [])
                   for param in update_body.additional_info.keys())):
        need_retrain = True
    else:
        need_retrain = False

    # Update parameters
    new_parameters = {**db_plugin.parameters, **update_body.parameters}
    db_plugin = plugin_crud.update_parameters(db, db_plugin, new_parameters)

    # Update additional info
    new_additional_info = {**db_plugin.additional_info, **update_body.additional_info}
    db_plugin = plugin_crud.update_additional_info(db, db_plugin, new_additional_info)

    # Restart training
    need_retrain and retrain_plugin(db, db_project, db_plugin)

    return {
        "message": "Plugin is updated successfully",
        "plugin": db_plugin
    }


def process_plugin_tigger(plugin_id: int, trigger_type: str, db: Session) -> dict:
    if trigger_type not in {"enable", "disable"}:
        raise HTTPException(status_code=400, detail=ErrorType.PLUGIN_TRIGGER_TYPE_NOT_VALID)
    db_plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
    validation_plugin_status(db, db_plugin)

    if trigger_type == "disable" and db_plugin.disabled is True:
        raise HTTPException(status_code=400, detail=ErrorType.PLUGIN_ALREADY_DISABLED)
    elif trigger_type == "enable" and db_plugin.disabled is False:
        raise HTTPException(status_code=400, detail=ErrorType.PLUGIN_ALREADY_ENABLED)

    if trigger_type == "disable":
        db_plugin = plugin_crud.disable_plugin(db, db_plugin)
    else:
        db_plugin = plugin_crud.enable_plugin(db, db_plugin)

    return {
        "message": f"Plugin is {trigger_type}d successfully",
        "plugin": db_plugin
    }
