import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

import core.crud.project as project_crud
import core.models.plugin as plugin_model
import core.models.project as project_model
from core.enums.error import ErrorType
from core.enums.status import PluginStatus

# Enable logging
logger = logging.getLogger(__name__)


def validation_plugin_status(db: Session, db_plugin: plugin_model.Plugin) -> project_model.Project:
    db_project = project_crud.get_project_by_id(db, db_plugin.project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail=ErrorType.PROJECT_NOT_FOUND)
    if db_project.status != PluginStatus.TRAINED:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_READY)
    if not db_plugin:
        raise HTTPException(status_code=404, detail=ErrorType.PLUGIN_NOT_FOUND)
    if db_plugin.status != PluginStatus.TRAINED:
        raise HTTPException(status_code=400, detail=ErrorType.PLUGIN_NOT_READY)
    return db_project
