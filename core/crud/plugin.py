import logging

from sqlalchemy.orm import Session

import core.models.plugin as model
import core.schemas.plugin as schema
from core.enums.status import PluginStatus

# Enable logging
logger = logging.getLogger(__name__)


def get_plugins(db: Session, skip: int = 0, limit: int = 100) -> list[model.Plugin]:
    # Get all plugins
    return db.query(model.Plugin).offset(skip).limit(limit).all()  # type: ignore


def get_plugin_by_id(db: Session, plugin_id: int) -> model.Plugin | None:
    # Get a plugin by id
    return db.query(model.Plugin).filter_by(id=plugin_id).first()


def get_all_model_names(db: Session) -> list[str]:
    # Get all model names
    return [x[0] for x in db.query(model.Plugin.model_name).all()]


def create_plugin(db: Session, plugin: schema.PluginCreate, project_id: int) -> model.Plugin:
    # Create a plugin
    db_plugin = model.Plugin(**plugin.dict(), project_id=project_id)
    db.add(db_plugin)
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def update_status(db: Session, db_plugin: model.Plugin, status: str) -> model.Plugin:
    # Update a plugin's status
    db_plugin.status = status
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def update_parameters(db: Session, db_plugin: model.Plugin, parameters: dict) -> model.Plugin:
    # Update a plugin's parameters
    db_plugin.parameters = parameters
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def update_additional_info(db: Session, db_plugin: model.Plugin, additional_info: dict) -> model.Plugin:
    # Update a plugin's additional info
    db_plugin.additional_info = additional_info
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def set_plugin_error(db: Session, db_plugin: model.Plugin, error: str) -> model.Plugin:
    # Set error of a plugin
    db_plugin.status = PluginStatus.ERROR
    db_plugin.error = error
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def update_model_name(db: Session, db_plugin: model.Plugin, model_name: str) -> model.Plugin:
    # Update a plugin's model name
    db_plugin.model_name = model_name
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def delete_plugin(db: Session, db_plugin: model.Plugin) -> None:
    # Delete a plugin
    db.delete(db_plugin)
    db.commit()


def delete_all_plugins_by_project_id(db: Session, project_id: int) -> None:
    # Delete plugins by project id
    db.query(model.Plugin).filter_by(project_id=project_id).delete(synchronize_session="fetch")
    db.commit()
