import logging

import pandas as pd
from pandas import DataFrame
from sklearn.model_selection import GroupShuffleSplit
from sqlalchemy.orm import Session

import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.crud.event_log import set_datasets_name
from core.crud.project import set_project_error
from core.enums.definition import ColumnDefinition
from core.enums.transition import Transition
from core.functions.definition.util import get_defined_column_name
from core.functions.event_log.df import get_dataframe
from core.functions.general.file import get_new_path
from core.functions.message.sender import send_training_data_to_all_plugins

# Enable logging
logger = logging.getLogger(__name__)


def start_pre_processing(project_id: int, db: Session, db_event_log: event_log_model.EventLog) -> bool:
    # Start pre-processing the data
    training_data_name = pre_process_data(db, db_event_log)
    if not training_data_name:
        set_project_error(db, project_id, "Failed to pre-process the data")
        return False
    send_training_data_to_all_plugins(project_id, training_data_name)
    return True


def pre_process_data(db: Session, db_event_log: event_log_model.EventLog) -> str:
    # Pre-process the data
    result = ""

    try:
        # Split dataframe
        df = get_dataframe(db_event_log)
        splitter = GroupShuffleSplit(test_size=.20, n_splits=2, random_state=7)
        split = splitter.split(df, groups=df['Case ID'])
        train_indexes, simulation_indexes = next(split)
        training_df = df.iloc[train_indexes]
        simulation_df = df.iloc[simulation_indexes]

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


def get_filtered_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get filtered dataframe
    if not any(d == ColumnDefinition.TRANSITION for d in columns_definition.values()):
        return df
    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    if not transition_column:
        return df
    df = df[df[transition_column].str.upper() == Transition.COMPLETE]
    return df


def get_processed_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get processed dataframe
    filtered_df = get_filtered_dataframe(df, definition.columns_definition)
    timestamped_df = get_timestamped_dataframe(filtered_df, definition.columns_definition)
    # bool_df =
    # numbered_df =
    renamed_df = get_renamed_dataframe(df, definition.columns_definition)
    return renamed_df


def get_timestamped_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get timestamped dataframe, convert to Timestamp of pandas
    for k, v in columns_definition.items():
        if k in {ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP}:
            df[k] = pd.to_datetime(df[k])
    return df


def get_renamed_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get renamed dataframe
    needed_definitions = {ColumnDefinition.ACTIVITY,
                          ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP,
                          ColumnDefinition.RESOURCE, ColumnDefinition.DURATION, ColumnDefinition.COST,
                          ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT}
    columns_need_to_rename = {}
    for column in df.columns.tolist():
        if (definition := columns_definition.get(column, column)) in needed_definitions:
            columns_need_to_rename[column] = definition
    return df.rename(columns=columns_need_to_rename)


def label_for_outcome(data: str | int | float | bool) -> int:
    # Label for outcome
    if isinstance(data, (int, float)):
        return 1 if int(data) > 0 else 0

    if isinstance(data, str):
        if data.strip().lower() in {"true", "1", "yes", "y", "positive"}:
            return 1
        if any(data.strip().lower().startswith(pre) for pre in ["complete", "finish", "close", "success", "succeed"]):
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
