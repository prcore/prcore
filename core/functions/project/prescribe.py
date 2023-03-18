import logging
from datetime import datetime
from time import sleep
from typing import BinaryIO

import core.crud.project as project_crud
import core.models.project as project_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.enums.definition import ColumnDefinition
from core.enums.status import ProjectStatus, PluginStatus
from core.functions.common.dataset import get_renamed_dataframe
from core.functions.common.decorator import threaded
from core.functions.common.etc import random_str
from core.functions.common.file import delete_file, get_new_path
from core.functions.definition.util import get_defined_column_name
from core.functions.plugin.util import enhance_additional_infos, get_active_plugins
from core.functions.event_log.dataset import get_cases_result_skeleton, get_processed_dataframe_for_new_dataset
from core.functions.event_log.file import get_dataframe_from_file
from core.functions.message.sender import send_dataset_prescription_request_to_all_plugins
from core.functions.project.validation import validate_ongoing_dataset
from core.starters import memory
from core.starters.database import SessionLocal

# Enable logging
logger = logging.getLogger(__name__)


def get_ongoing_dataset_result_key(file: BinaryIO, extension: str, seperator: str,
                                   db_project: project_model.Project) -> str:
    # Get the result key of the ongoing dataset
    result = ""

    try:
        temp_path = get_new_path(f"{path.TEMP_PATH}/", suffix=f".{extension}")
        with open(temp_path, "wb") as f:
            f.write(file.read())

        # Get dataframe from file
        try:
            df = get_dataframe_from_file(temp_path, extension, seperator)
        finally:
            delete_file(temp_path)

        # Get the result skeleton
        columns = df.columns.tolist()
        columns_definition = db_project.event_log.definition.columns_definition
        case_attributes = db_project.event_log.definition.case_attributes

        # Check the columns definition
        validate_ongoing_dataset(columns, columns_definition, case_attributes)

        # Get a preprocessed dataframe and cases
        definition = definition_schema.Definition.from_orm(db_project.event_log.definition)
        df = get_processed_dataframe_for_new_dataset(df, definition)
        cases = get_cases_result_skeleton(df, get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID))
        cases_count = len(cases)
        additional_infos = enhance_additional_infos(
            additional_infos={plugin.key: plugin.additional_info for plugin in db_project.plugins},
            active_plugins=get_active_plugins(),
            definition=definition
        )

        # Send the result request to the plugins
        while (result_key := random_str(8)) in memory.ongoing_results:
            continue

        memory.ongoing_results[result_key] = {
            "date": datetime.now(),
            "project_id": db_project.id,
            "dataframe": df,
            "plugins": {plugin.key: plugin.id for plugin in db_project.plugins
                        if plugin.status != PluginStatus.ERROR and not plugin.disabled},
            "model_names": {plugin.id: plugin.model_name for plugin in db_project.plugins},
            "ongoing_df_name": "",
            "additional_infos": additional_infos,
            "results": {},
            "error": "",
            "cases_count": cases_count,
            "columns": columns,
            "columns_definition": columns_definition,
            "case_attributes": case_attributes,
            "cases": cases
        }

        result = result_key
    except ValueError as e:
        logger.error(f"Get ongoing dataset result key error: {e}")
    except Exception as e:
        logger.error(f"Get ongoing dataset result key error: {e}", exc_info=True)

    return result


def process_ongoing_dataset(result_key: str) -> bool:
    # Process the ongoing dataset
    result = False

    try:
        if result_key not in memory.ongoing_results:
            raise ValueError("Result key not found")

        # Get the data
        data = memory.ongoing_results[result_key]
        project_id = data["project_id"]
        df = data["dataframe"]
        plugins = data["plugins"]
        model_names = data["model_names"]
        columns_definition = data["columns_definition"]
        case_attributes = data["case_attributes"]
        additional_infos = data["additional_infos"]

        # Get renamed df and save it to the temp path
        df = get_renamed_dataframe(df, columns_definition, case_attributes)
        temp_path = get_new_path(f"{path.TEMP_PATH}/", suffix=".pkl")
        df.to_pickle(temp_path)
        temp_csv_path = temp_path.replace(".pkl", ".csv")
        df.to_csv(temp_csv_path, index=False)
        ongoing_df_name = temp_path.split("/")[-1].split(".")[0]
        memory.ongoing_results[result_key]["ongoing_df_name"] = temp_path.split("/")[-1].split(".")[0]

        # Send the dataset to the plugins
        send_dataset_prescription_request_to_all_plugins(plugins, project_id, model_names, result_key, ongoing_df_name,
                                                         additional_infos)
        result = True
    except ValueError as e:
        logger.error(f"Process ongoing dataset error: {e}")
    except Exception as e:
        logger.error(f"Process ongoing dataset error: {e}", exc_info=True)

    return result


def delete_result_from_memory(result_key: str) -> bool:
    # Delete the result from memory
    result = False

    try:
        if result_key in memory.ongoing_results:
            del memory.ongoing_results[result_key]
            result = True
    except Exception as e:
        logger.error(f"Delete result from memory error: {e}", exc_info=True)

    return result


@threaded()
def run_project_watcher_for_ongoing_dataset(project_id: int, result_key: str) -> bool:
    # Watch the project status, and start to prescribe if the project is ready
    while True:
        with SessionLocal() as db:
            db_project = project_crud.get_project_by_id(db, project_id)
            if not db_project:
                return False
            if db_project.status in {ProjectStatus.TRAINED, ProjectStatus.STREAMING, ProjectStatus.SIMULATING}:
                if result_key not in memory.ongoing_results:
                    return False
                ongoing_result = memory.ongoing_results[result_key]
                ongoing_result["plugins"] = {plugin.key: plugin.id for plugin in db_project.plugins
                                             if plugin.status in {PluginStatus.TRAINED, PluginStatus.STREAMING}
                                             and not plugin.disabled}
                ongoing_result["model_names"] = {plugin.id: plugin.model_name for plugin in db_project.plugins}
                break
            sleep(5)
    return process_ongoing_dataset(result_key)
