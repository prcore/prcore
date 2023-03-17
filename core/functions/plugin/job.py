import logging

from sqlalchemy.orm import Session

import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
import core.models.plugin as plugin_model
import core.models.project as project_model
import core.schemas.definition as definition_schema
from core.enums.status import PluginStatus
from core.functions.message.sender import send_training_data
from core.functions.plugin.util import enhance_additional_info, get_active_plugins

# Enable logging
logger = logging.getLogger(__name__)


def retrain_plugin(db: Session, db_project: project_model.Project, db_plugin: plugin_model.Plugin) -> None:
    project_crud.update_status(db, db_project, PluginStatus.TRAINING)
    plugin_crud.update_status(db, db_plugin, PluginStatus.TRAINING)
    additional_info = enhance_additional_info(db_plugin.additional_info,
                                              get_active_plugins().get(db_plugin.key, {}),
                                              definition_schema.Definition.from_orm(
                                                  db_project.event_log.definition))
    send_training_data(db_plugin.key, db_project.id, db_plugin.id, db_project.event_log.training_df_name,
                       db_plugin.parameters,
                       additional_info)
