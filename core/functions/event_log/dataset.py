import logging
import json

from pandas import DataFrame
from sklearn.model_selection import GroupShuffleSplit
from sqlalchemy.orm import Session

import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.crud.event_log import set_datasets_name
from core.crud.project import set_project_error
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_column_definition, get_defined_column_name
from core.functions.event_log.df import get_dataframe
from core.functions.general.file import get_new_path
from core.functions.message.sender import send_training_data_to_all_plugins
from core.starters import memory

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
        processed_df = get_processed_df(training_df, db_event_log.definition)

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


def get_processed_df(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get processed dataframe
    renamed_df = get_renamed_df(df, definition)
    return renamed_df


def get_renamed_df(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get renamed dataframe
    special_definitions = {ColumnDefinition.ACTIVITY, ColumnDefinition.TIMESTAMP,
                           ColumnDefinition.TRANSITION, ColumnDefinition.START_TIMESTAMP,
                           ColumnDefinition.END_TIMESTAMP, ColumnDefinition.RESOURCE, ColumnDefinition.DURATION,
                           ColumnDefinition.COST, ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT}
    columns_need_to_rename = {}
    for column in df.columns.tolist():
        if (special_definition := get_column_definition(column, definition.columns_definition)) in special_definitions:
            columns_need_to_rename[column] = special_definition.value
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


def get_cases(df: DataFrame, definition: definition_schema.Definition) -> dict[str, list[dict]]:
    cases = {}
    columns = df.columns.tolist()
    special_definitions = {ColumnDefinition.ACTIVITY, ColumnDefinition.TIMESTAMP,
                           ColumnDefinition.TRANSITION, ColumnDefinition.START_TIMESTAMP,
                           ColumnDefinition.END_TIMESTAMP, ColumnDefinition.RESOURCE, ColumnDefinition.DURATION,
                           ColumnDefinition.COST}
    case_id_column_name = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)

    for case_id, events_df in df.groupby(case_id_column_name):
        case_identifier = str(case_id)
        events = []
        for _, row in events_df.iterrows():
            event = {}
            for column in columns:
                if get_column_definition(column, definition.columns_definition) == ColumnDefinition.CASE_ID:
                    continue
                if get_column_definition(column, definition.columns_definition) in special_definitions:
                    event[get_column_definition(column, definition.columns_definition).value] = row[column]
            events.append(event)
        cases[case_identifier] = events

    return cases
