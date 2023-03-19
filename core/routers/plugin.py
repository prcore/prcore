import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import core.schemas.request.plugin as plugin_request
import core.schemas.response.plugin as plugin_response
from core.functions.common.request import get_real_ip, get_db
from core.security.token import validate_token
from core.services.plugin import (process_plugins_reading, process_plugin_reading,
                                  process_available_plugins_reading, process_plugin_update, process_plugin_tigger)

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/plugin")


@router.get("/all", response_model=plugin_response.AllPluginsResponse)
def read_plugins(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                 _: bool = Depends(validate_token)):
    logger.warning(f"Read plugins - from IP {get_real_ip(request)}")
    return process_plugins_reading(skip, limit, db)


@router.get("/available", response_model=plugin_response.AvailablePluginsResponse)
def read_available_plugins(request: Request, _: bool = Depends(validate_token)):
    logger.warning(f"Get available plugins - from IP {get_real_ip(request)}")
    return process_available_plugins_reading()


@router.get("/{plugin_id}", response_model=plugin_response.PluginResponse)
def read_plugin(request: Request, plugin_id: int, db: Session = Depends(get_db),
                _: bool = Depends(validate_token)):
    logger.warning(f"Read plugin {plugin_id} - from IP {get_real_ip(request)}")
    return process_plugin_reading(plugin_id, db)


@router.put("/{plugin_id}", response_model=plugin_response.PluginResponse)
def update_plugin(request: Request, plugin_id: int, update_body: plugin_request.UpdatePluginRequest,
                  _: bool = Depends(validate_token), db: Session = Depends(get_db)):
    logger.warning(f"Update plugin {plugin_id}  - from IP {get_real_ip(request)}")
    return process_plugin_update(plugin_id, update_body, db)


@router.put("/{plugin_id}/{trigger_type}", response_model=plugin_response.PluginResponse)
def tigger_plugin(request: Request, plugin_id: int, trigger_type: str,
                  db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Disable or enable plugin {plugin_id} - from IP {get_real_ip(request)}")
    return process_plugin_tigger(plugin_id, trigger_type, db)
