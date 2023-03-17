import logging
from time import sleep

from sklearn.model_selection import GroupShuffleSplit
from sqlalchemy.orm import Session

import core.crud.definition as definition_crud
import core.crud.event_log as event_log_crud
import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
import core.schemas.plugin as plugin_schema
import core.schemas.request.event_log as event_log_request
from core.confs import path
from core.enums.definition import ColumnDefinition
from core.enums.status import PluginStatus
from core.functions.common.file import delete_file, get_new_path, get_dataframe_from_pickle
from core.functions.definition.util import get_defined_column_name
from core.functions.event_log.df import get_dataframe, get_dataframe_by_id_or_name
from core.functions.event_log.validation import validate_columns_definition, validate_case_attributes
from core.functions.message.sender import send_training_data_to_all_plugins, send_process_request
from core.functions.plugin.util import get_parameters_for_plugin, enhance_additional_infos
from core.functions.project.streaming import disable_streaming
from core.starters import memory
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
        event_log_id = db_project.event_log.id
        df_name = db_project.event_log.df_name

    training_df_name = pre_process_data(event_log_id, df_name, definition)

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
                plugin_parameters = get_parameters_for_plugin(db_plugin.key, active_plugins, parameters)
                plugin_crud.update_parameters(db, db_plugin, plugin_parameters)
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
        send_training_data_to_all_plugins(plugins, project_id, training_df_name, parameters, additional_infos)

    return True


def pre_process_data(event_log_id: int, df_name: str, definition: definition_schema.Definition) -> str:
    # Pre-process the data
    result = ""

    try:
        # Split dataframe
        df = get_dataframe_by_id_or_name(event_log_id, df_name)
        case_id_column_name = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)
        splitter = GroupShuffleSplit(test_size=0.2, n_splits=1, random_state=42)
        split = splitter.split(df, groups=df[case_id_column_name])
        train_indices, simulation_indices = next(split)
        training_df = df.iloc[train_indices]
        simulation_df = df.iloc[simulation_indices]

        # Get processed dataframe for training
        temp_path = get_new_path(base_path=f"{path.TEMP_PATH}/", suffix=".pkl")
        training_df.to_pickle(temp_path)
        request_key = send_process_request(temp_path.split("/")[-1], definition)
        while not memory.pending_dfs[request_key]["finished"]:
            sleep(1)
        processed_df_path = f"{path.TEMP_PATH}/{memory.pending_dfs[request_key].get('processed_df')}"
        processed_df = get_dataframe_from_pickle(processed_df_path)
        delete_file(processed_df_path)
        memory.pending_dfs.pop(request_key)
        if processed_df is None:
            raise FileNotFoundError("Processed dataframe not found")

        # Save the data
        training_df_path = get_new_path(base_path=f"{path.EVENT_LOG_TRAINING_DF_PATH}/", suffix=".pkl")
        processed_df.to_pickle(training_df_path)
        training_csv_path = training_df_path.replace(".pkl", ".csv")
        processed_df.to_csv(training_csv_path, index=False)
        simulation_df_path = get_new_path(base_path=f"{path.EVENT_LOG_SIMULATION_DF_PATH}/", suffix=".pkl")
        simulation_df.to_pickle(simulation_df_path)

        # Update the database
        training_df_name = training_df_path.split("/")[-1].split(".")[0]
        simulation_df_name = simulation_df_path.split("/")[-1]
        with SessionLocal() as db:
            event_log_crud.set_datasets_name(db, event_log_id, training_df_name, simulation_df_name)
        result = training_df_name
    except Exception as e:
        logger.warning(f"Pre-processing failed: {e}", exc_info=True)

    return result
