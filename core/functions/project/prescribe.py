import logging
from datetime import datetime

from fastapi import UploadFile

import core.models.project as project_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_defined_column_name
from core.functions.event_log.dataset import (get_cases_result_skeleton, get_new_processed_dataframe,
                                              get_renamed_dataframe)
from core.functions.event_log.file import get_dataframe_from_file
from core.functions.general.etc import random_str
from core.functions.general.file import delete_file, get_new_path
from core.functions.message.sender import send_ongoing_dataset_to_all_plugins
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def get_ongoing_dataset_result_key(file: UploadFile, extension: str, seperator: str,
                                   db_project: project_model.Project) -> str:
    # Get the result key of the ongoing dataset
    result = ""

    try:
        temp_path = get_new_path(f"{path.TEMP_PATH}/", suffix=f".{extension}")
        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        # Get dataframe from file
        try:
            df = get_dataframe_from_file(temp_path, extension, seperator)
        finally:
            delete_file(temp_path)

        # Get the result skeleton
        columns = df.columns.tolist()
        columns_definition = db_project.event_log.definition.columns_definition

        # Check the columns definition
        for column in columns_definition:
            if columns_definition.get(column) and column not in columns:
                raise ValueError(f"Column is defined but not in the new dataset: {column}")

        # Get a preprocessed dataframe and cases
        definition = definition_schema.Definition.from_orm(db_project.event_log.definition)
        df = get_new_processed_dataframe(df, definition)
        cases = get_cases_result_skeleton(df, get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID))
        cases_count = len(cases)

        # Send the result request to the plugins
        while (result_key := random_str(8)) in memory.ongoing_results:
            continue

        memory.ongoing_results[result_key] = {
            "date": datetime.now(),
            "project_id": db_project.id,
            "dataframe": df,
            "plugins": {plugin.key: plugin.id for plugin in db_project.plugins},
            "model_names": {plugin.id: plugin.model_name for plugin in db_project.plugins},
            "ongoing_df_name": "",
            "results": {},
            "error": "",
            "cases_count": cases_count,
            "columns": columns,
            "columns_definition": columns_definition,
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

        # Get renamed df and save it to the temp path
        df = get_renamed_dataframe(df, columns_definition)
        temp_path = get_new_path(f"{path.TEMP_PATH}/", suffix=".pkl")
        df.to_pickle(temp_path)
        temp_csv_path = temp_path.replace(".pkl", ".csv")
        df.to_csv(temp_csv_path, index=False)
        ongoing_df_name = temp_path.split("/")[-1].split(".")[0]
        memory.ongoing_results[result_key]["ongoing_df_name"] = temp_path.split("/")[-1].split(".")[0]

        # Send the dataset to the plugins
        send_ongoing_dataset_to_all_plugins(project_id, plugins, model_names, result_key, ongoing_df_name)
        result = True
    except ValueError as e:
        logger.error(f"Process ongoing dataset error: {e}")
    except Exception as e:
        logger.error(f"Process ongoing dataset error: {e}", exc_info=True)

    return result
