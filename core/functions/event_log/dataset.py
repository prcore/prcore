import logging
from random import randint

import numpy as np
import pandas as pd
from pandas import DataFrame

import core.models.event_log as event_log_model
from core.confs import path
from core.enums.definition import ColumnDefinition, Transition
from core.functions.common.dataset import get_timestamped_dataframe, get_transition_recognized_dataframe
from core.functions.common.file import copy_file, get_new_path
from core.functions.definition.util import get_defined_column_name, get_start_timestamp
from core.schemas import definition as definition_schema

# Enable logging
logger = logging.getLogger(__name__)


def get_completed_transition_df(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get completed transition dataframe
    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)

    if not transition_column:
        return df

    if not np.any(df[transition_column] == Transition.COMPLETE):
        return df

    return df[df[transition_column] == Transition.COMPLETE]


def get_original_dataset_path(db_event_log: event_log_model.EventLog) -> str:
    # Get original dataset path for testing purpose
    result = ""

    try:
        saved_name = db_event_log.saved_name
        temp_path = get_new_path(path.TEMP_PATH, suffix=f".{saved_name.split('.')[-1]}")
        copy_result = copy_file(f"{path.EVENT_LOG_RAW_PATH}/{saved_name}", temp_path)
        result = temp_path if copy_result else ""
    except Exception as e:
        logger.error(f"Error occurred when getting original dataset path: {e}")

    return result


def get_processed_dataset_path(db_event_log: event_log_model.EventLog) -> str:
    # Get processed dataset path for testing purpose
    result = ""

    try:
        temp_path = get_new_path(path.TEMP_PATH, suffix=".csv")
        training_df = pd.read_pickle(f"{path.EVENT_LOG_TRAINING_DF_PATH}/{db_event_log.training_df_name}.pkl")
        training_df.to_csv(temp_path, index=False)
        result = temp_path
    except Exception as e:
        logger.error(f"Error occurred when getting processed dataset path: {e}")

    return result


def get_ongoing_dataset_path(db_event_log: event_log_model.EventLog) -> str:
    # Get ongoing dataset path for testing purpose
    result = ""

    try:
        temp_path = get_new_path(path.TEMP_PATH, suffix=".csv")
        simulation_df = pd.read_pickle(f"{path.EVENT_LOG_SIMULATION_DF_PATH}/{db_event_log.simulation_df_name}")
        case_id_column = get_defined_column_name(db_event_log.definition.columns_definition, ColumnDefinition.CASE_ID)
        grouped_df = simulation_df.groupby(case_id_column)
        ongoing_cases = []
        columns = simulation_df.columns.tolist()
        for _, group in grouped_df:
            values = group.values
            if group.shape[0] < 4:
                continue
            length = randint(3, group.shape[0] - 1)
            ongoing_cases.extend(values[:length])
        ongoing_cases_df = pd.DataFrame(ongoing_cases, columns=columns)
        ongoing_cases_df.to_csv(temp_path, index=False)
        result = temp_path
    except Exception as e:
        logger.warning(f"Get ongoing dataset path failed: {e}")

    return result


def get_simulation_dataset_path(db_event_log: event_log_model.EventLog) -> str:
    # Get simulation dataset path for testing purpose
    result = ""

    try:
        temp_path = get_new_path(path.TEMP_PATH, suffix=".csv")
        simulation_df = pd.read_pickle(f"{path.EVENT_LOG_SIMULATION_DF_PATH}/{db_event_log.simulation_df_name}")
        simulation_df.to_csv(temp_path, index=False)
        result = temp_path
    except Exception as e:
        logger.error(f"Error occurred when getting simulation dataset path: {e}")

    return result


def get_cases_result_skeleton(df: DataFrame, case_id_column: str) -> dict[str, dict[str, list]]:
    # Get cases result skeleton
    result = {}
    grouped_df = df.groupby(case_id_column)
    for case_id, group in grouped_df:
        result[str(case_id)] = {
            "prescriptions": [],
            "events": group.values.tolist()
        }
    return result


def get_processed_dataframe_for_new_dataset(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get new processed dataframe
    df = df.astype(str)
    timestamp_column = get_start_timestamp(definition.columns_definition)
    df = get_timestamped_dataframe(df, definition.columns_definition)
    df = get_transition_recognized_dataframe(df, definition)
    df.sort_values(by=timestamp_column, inplace=True)
    df = df.astype(str)
    return df
