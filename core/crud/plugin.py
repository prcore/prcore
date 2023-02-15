import logging

from sqlalchemy.orm import Session

import core.models.plugin as model
import core.schemas.plugin as schema

# Enable logging
logger = logging.getLogger("prcore")


def get_plugins(db: Session, skip: int = 0, limit: int = 100) -> list[model.Plugin]:
    # Get all plugins
    return db.query(model.Plugin).offset(skip).limit(limit).all()  # type: ignore


def get_plugin_by_id(db: Session, plugin_id: int) -> model.Plugin | None:
    # Get a plugin by id
    return db.query(model.Plugin).filter_by(id=plugin_id).first()


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


def update_model_name(db: Session, db_plugin: model.Plugin, model_name: str) -> model.Plugin:
    # Update a plugin's model name
    db_plugin.model_name = model_name
    db.commit()
    db.refresh(db_plugin)
    return db_plugin


def delete_plugin(db: Session, plugin_id: int) -> None:
    # Delete a plugin
    db_plugin = get_plugin_by_id(db, plugin_id=plugin_id)
    if db_plugin:
        db.delete(db_plugin)
        db.commit()
    return db_plugin
