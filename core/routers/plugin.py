import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import core.crud.plugin as plugin_crud
import core.schemas.response.plugin as plugin_response
from core.functions.general.request import get_real_ip, get_db
from core.functions.plugin.util import get_active_plugins
from core.functions.plugin.validation import validation_plugin_status
from core.security.token import validate_token

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/plugin")


@router.get("/all", response_model=plugin_response.AllPluginsResponse)
def read_plugins(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                 _: bool = Depends(validate_token)):
    logger.warning(f"Read plugins - from IP {get_real_ip(request)}")
    return {
        "message": "Plugins retrieved successfully",
        "plugins": plugin_crud.get_plugins(db, skip=skip, limit=limit)
    }


@router.get("/available", response_model=plugin_response.AvailablePluginsResponse)
def read_available_plugins(request: Request, _: bool = Depends(validate_token)):
    logger.warning(f"Get available plugins - from IP {get_real_ip(request)}")
    return {
        "message": "Available plugins retrieved successfully",
        "plugins": get_active_plugins()
    }


@router.put("/{plugin_id}/disable", response_model=plugin_response.PluginResponse)
def disable_plugin(request: Request, plugin_id: int, db: Session = Depends(get_db),
                   _: bool = Depends(validate_token)):
    logger.warning(f"Disable plugin {plugin_id} - from IP {get_real_ip(request)}")
    db_plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
    validation_plugin_status(db_plugin)
    return {
        "message": "Plugin disabled successfully",
        "plugin": plugin_crud.disable_plugin(db, db_plugin)
    }


@router.put("/{plugin_id}/enable", response_model=plugin_response.PluginResponse)
def enable_plugin(request: Request, plugin_id: int, db: Session = Depends(get_db),
                  _: bool = Depends(validate_token)):
    logger.warning(f"Enable plugin {plugin_id} - from IP {get_real_ip(request)}")
    db_plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
    validation_plugin_status(db_plugin)
    return {
        "message": "Plugin enabled successfully",
        "plugin": plugin_crud.enable_plugin(db, db_plugin)
    }
