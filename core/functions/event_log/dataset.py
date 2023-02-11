import logging

import pandas as pd
from pandas import DataFrame
from sklearn.model_selection import GroupShuffleSplit
from sqlalchemy.orm import Session

import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.crud.event_log import set_datasets_name
from core.enums.definition import ColumnDefinition, DefinitionType
from core.enums.transition import Transition
from core.functions.definition.util import get_defined_column_name
from core.functions.event_log.df import get_dataframe
from core.functions.general.file import get_new_path

# Enable logging
logger = logging.getLogger(__name__)


def pre_process_data(db: Session, db_event_log: event_log_model.EventLog) -> str:
    # Pre-process the data
    result = ""

    try:
        # Split dataframe
        df = get_dataframe(db_event_log)
        case_id_column_name = get_defined_column_name(db_event_log.definition.columns_definition,
                                                      ColumnDefinition.CASE_ID)
        splitter = GroupShuffleSplit(test_size=0.2, n_splits=1, random_state=42)
        split = splitter.split(df, groups=df[case_id_column_name])
        train_indices, simulation_indices = next(split)
        training_df = df.iloc[train_indices]
        simulation_df = df.iloc[simulation_indices]

        # Get processed dataframe for training
        processed_df = get_processed_dataframe(training_df, db_event_log.definition)

        # Save the data
        training_df_path = get_new_path(base_path=f"{path.EVENT_LOG_TRAINING_DATA_PATH}/", suffix=".pkl")
        training_df_name = training_df_path.split("/")[-1]
        simulation_df_path = get_new_path(base_path=f"{path.EVENT_LOG_SIMULATION_DF_PATH}/", suffix=".pkl")
        simulation_df_name = simulation_df_path.split("/")[-1]
        processed_df.to_pickle(training_df_path)
        simulation_df.to_pickle(simulation_df_path)

        # Update the database
        set_datasets_name(db, db_event_log, training_df_name, simulation_df_name)
        result = training_df_name
    except Exception as e:
        logger.warning(f"Pre-processing failed: {e}", exc_info=True)

    return result


def get_processed_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get processed dataframe
    filtered_df = get_filtered_dataframe(df, definition.columns_definition)
    timestamped_df = get_timestamped_dataframe(filtered_df, definition.columns_definition)
    numbered_df = get_numbered_dataframe(timestamped_df, definition.columns_definition)
    bool_df = get_bool_dataframe(numbered_df, definition.columns_definition)
    duration_added_df = get_duration_added_dataframe(bool_df, definition.columns_definition)
    outcome_and_treatment_dataframe = get_outcome_and_treatment_dataframe(duration_added_df, definition)
    renamed_df = get_renamed_dataframe(outcome_and_treatment_dataframe, definition.columns_definition)
    return renamed_df


def get_filtered_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get filtered dataframe
    if not any(d == ColumnDefinition.TRANSITION for d in columns_definition.values()):
        return df
    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    df = df[df[transition_column].str.upper() == Transition.COMPLETE]
    return df


def get_timestamped_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get timestamped dataframe, convert to Timestamp of pandas
    for k, v in columns_definition.items():
        if v in {ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP}:
            df = df.copy()
            df.loc[:, k] = pd.to_datetime(df[k], errors="coerce")
    return df


def get_numbered_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get numbered dataframe
    for k, v in columns_definition.items():
        if v in DefinitionType.NUMBER:
            df = df.copy()
            df.loc[:, k] = pd.to_numeric(df[k], errors="coerce")
    return df


def get_bool_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get bool dataframe
    for k, v in columns_definition.items():
        if v in DefinitionType.BOOLEAN:
            df[k] = pd.to_numeric(df[k], errors="coerce").astype(bool)
    return df


def get_duration_added_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get duration added dataframe
    case_id_column = get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID)
    timestamp_column = get_defined_column_name(columns_definition, ColumnDefinition.TIMESTAMP)
    start_time_column = get_defined_column_name(columns_definition, ColumnDefinition.START_TIMESTAMP)
    end_time_column = get_defined_column_name(columns_definition, ColumnDefinition.END_TIMESTAMP)
    duration_column = get_defined_column_name(columns_definition, ColumnDefinition.DURATION)
    if duration_column:
        return get_duration_added_df_by_original_data(df, duration_column)
    elif timestamp_column:
        return get_duration_added_df_by_timestamp(df, case_id_column, timestamp_column)
    elif start_time_column and end_time_column:
        return get_duration_added_df_by_start_end_timestamp(df, case_id_column, start_time_column, end_time_column)
    else:
        return df


def get_duration_added_df_by_original_data(df: DataFrame, duration_column: str) -> DataFrame:
    # Get duration added dataframe by original data
    df[duration_column] = df[duration_column].transform(lambda x: int(pd.to_timedelta(x).total_seconds()))
    return df


def get_duration_added_df_by_timestamp(df: DataFrame, case_id_column: str, timestamp_column: str) -> DataFrame:
    groups = df.groupby(case_id_column)[timestamp_column].agg(["min", "max"])
    groups["DURATION"] = (groups["max"] - groups["min"]).dt.total_seconds().astype(int)
    df = df.merge(groups[["DURATION"]], left_on=case_id_column, right_index=True)
    del groups
    return df


def get_duration_added_df_by_start_end_timestamp(df: DataFrame, case_id_column: str,
                                                 start_time_column: str, end_time_column: str) -> DataFrame:
    # Get duration added dataframe by start and end timestamp
    df = df.sort_values(by=[start_time_column, end_time_column])
    grouped = df.groupby(case_id_column).agg({start_time_column: "first", end_time_column: "last"})
    grouped["DURATION"] = grouped[end_time_column] - grouped[start_time_column]
    grouped["DURATION"] = grouped["DURATION"].dt.total_seconds().astype(int)
    df = df.merge(grouped[["DURATION"]], left_on=case_id_column, right_index=True)
    return df


def convert_to_seconds(time_str):
    time_str = str(time_str).strip().lower()
    if time_str.isdigit():
        return int(time_str)

    value = ""
    unit = ""
    for char in time_str:
        if char.isdigit():
            value += char
        else:
            unit += char
    value = int(value)
    if unit in ["months", "month", "mo", "m"]:
        return value * 30 * 24 * 60 * 60
    elif unit in ["weeks", "week", "wk", "w"]:
        return value * 7 * 24 * 60 * 60
    elif unit in ["days", "day", "d"]:
        return value * 24 * 60 * 60
    elif unit in ["hours", "hour", "hr", "h"]:
        return value * 60 * 60
    elif unit in ["minutes", "minute", "min", "m"]:
        return value * 60
    elif unit in ["seconds", "second", "sec", "s"]:
        return value
    else:
        raise ValueError("Invalid unit")


def get_outcome_and_treatment_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get outcome and treatment dataframe
    return df


def get_renamed_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get renamed dataframe
    needed_definitions = {ColumnDefinition.CASE_ID,
                          ColumnDefinition.ACTIVITY,
                          ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP,
                          ColumnDefinition.RESOURCE, ColumnDefinition.DURATION, ColumnDefinition.COST,
                          ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT}
    columns_need_to_rename = {}
    for column in df.columns.tolist():
        if (definition := columns_definition.get(column, column)) in needed_definitions:
            columns_need_to_rename[column] = definition
    df = df.rename(columns=columns_need_to_rename)
    df.drop(columns=[c for c in df.columns if c not in needed_definitions], axis=1, inplace=True)
    return df


def label_for_outcome(data: str | int | float | bool) -> int:
    # Label for outcome
    if isinstance(data, (int, float)):
        return 1 if int(data) > 0 else 0

    if isinstance(data, str):
        stripped_data = data.strip().lower()
        if stripped_data in {"true", "1", "yes", "y", "positive"}:
            return 1
        if any(stripped_data.startswith(pre) for pre in ["complete", "finish", "close", "success", "succeed"]):
            return 1
        return 0

    if isinstance(data, bool):
        return 1 if data else 0

    raise ValueError(f"Unknown data: {data}")


def assign_outcome_label(group: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Assign outcome label
    pre_defined_outcome_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.OUTCOME)
    if pre_defined_outcome_column:
        group[pre_defined_outcome_column] = group.apply(
            lambda row: label_for_outcome(row[pre_defined_outcome_column]),
            axis=1
        )
    else:
        pass
    return group


def assign_treatment_label(group: DataFrame) -> DataFrame:
    # Assign treatment label
    group['treatment'] = group['treatment'].fillna(0)
    group['treatment'] = group['treatment'].astype(int)
    return group
