import logging

from sqlalchemy.orm import Session

import core.crud.definition as definition_crud
import core.crud.event_log as event_log_crud
import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
import core.schemas.plugin as plugin_schema
import core.schemas.request.event_log as event_log_request
from core.enums.status import PluginStatus
from core.functions.event_log.dataset import pre_process_data
from core.functions.event_log.df import get_dataframe
from core.functions.event_log.validation import validate_columns_definition, validate_case_attributes
from core.functions.message.sender import send_training_data_to_all_plugins
from core.functions.plugin.util import get_parameters_for_plugin, enhance_additional_infos
from core.functions.project.streaming import disable_streaming
from core.starters.database import SessionLocal

# Enable logging
logger = logging.getLogger(__name__)


def set_definition(db: Session, db_event_log: event_log_model.EventLog,
                   update_body: event_log_request.ColumnsDefinitionRequest) -> event_log_model.EventLog:
    df = get_dataframe(db_event_log)
    validate_columns_definition(update_body.columns_definition, df)
    validate_case_attributes(update_body.case_attributes, df)

    if db_event_log.definition:
        db_definition = definition_crud.update_definition(db, definition_schema.Definition(
            id=db_event_log.definition.id,
            created_at=db_event_log.definition.created_at,
            columns_definition=update_body.columns_definition,
            case_attributes=update_body.case_attributes,
            fast_mode=update_body.fast_mode,
            start_transition=update_body.start_transition,
            complete_transition=update_body.complete_transition,
            abort_transition=update_body.abort_transition,
            outcome_definition=None,
            treatment_definition=None
        ))
        db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)
        db_project and disable_streaming(db, db_project, redefined=True)
    else:
        db_definition = definition_crud.create_definition(db, definition_schema.DefinitionCreate(
            columns_definition=update_body.columns_definition,
            case_attributes=update_body.case_attributes,
            fast_mode=update_body.fast_mode,
            start_transition=update_body.start_transition,
            complete_transition=update_body.complete_transition,
            abort_transition=update_body.abort_transition
        ))

    return event_log_crud.associate_definition(db, db_event_log, db_definition.id)


def start_pre_processing(project_id: int, active_plugins: dict, parameters: dict, additional_infos: dict,
                         redefined: bool = False) -> bool:
    # Start pre-processing the data
    with SessionLocal() as db:
        db_project = project_crud.get_project_by_id(db, project_id)
        if not db_project:
            return False
        definition = definition_schema.Definition.from_orm(db_project.event_log.definition)
        training_df_name = pre_process_data(db_project.event_log.id, db_project.event_log.df_name, definition)

    with SessionLocal() as db:
        db_project = project_crud.get_project_by_id(db, project_id)
        if not db_project:
            return False

        if not training_df_name:
            project_crud.set_project_error(db, db_project, "Failed to pre-process the data")
            return False

        plugin_keys = list(active_plugins.keys())
        plugins = {}

        if redefined:
            for db_plugin in db_project.plugins:
                plugin_crud.update_status(db, db_plugin, PluginStatus.PREPROCESSING)
                parameters = get_parameters_for_plugin(db_plugin.key, active_plugins, parameters)
                plugin_crud.update_parameters(db, db_plugin, parameters)
                plugin_crud.update_additional_info(db, db_plugin, additional_infos.get(db_plugin.key, {}))
            plugins = {plugin.key: plugin.id for plugin in db_project.plugins}
        else:
            for plugin_key in plugin_keys:
                db_plugin = plugin_crud.create_plugin(
                    db=db,
                    plugin=plugin_schema.PluginCreate(
                        key=plugin_key,
                        prescription_type=active_plugins[plugin_key]["prescription_type"],
                        name=active_plugins[plugin_key]["name"],
                        description=active_plugins[plugin_key]["description"],
                        parameters=get_parameters_for_plugin(plugin_key, active_plugins, parameters),
                        additional_info=additional_infos.get(plugin_key, {}),
                        status=PluginStatus.WAITING
                    ),
                    project_id=project_id
                )
                plugins[plugin_key] = db_plugin.id

        additional_infos = enhance_additional_infos(
            additional_infos=additional_infos,
            active_plugins=active_plugins,
            definition=definition_schema.Definition.from_orm(db_project.event_log.definition)
        )
        send_training_data_to_all_plugins(plugins, project_id, training_df_name, additional_infos)

    return True
