import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import core.crud.plugin as plugin_crud
import core.responses.plugin as plugin_response
from core.starters.database import get_db
from core.functions.general.etc import get_real_ip
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
        "projects": plugin_crud.get_plugins(db, skip=skip, limit=limit)
    }
