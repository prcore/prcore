import logging

import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from sklearn.model_selection import GroupShuffleSplit
from sqlalchemy.orm import Session

import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.crud.event_log import set_datasets_name
from core.enums.definition import ColumnDefinition, DefinitionType, Transition
from core.functions.definition.condition import check_or_conditions
from core.functions.definition.util import get_defined_column_name
from core.functions.event_log.df import get_dataframe
from core.functions.general.file import get_new_path

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
        processed_df = get_processed_dataframe(
            df=training_df,
            definition=definition_schema.Definition.from_orm(db_event_log.definition),
        )

        # Save the data
        training_df_path = get_new_path(base_path=f"{path.EVENT_LOG_TRAINING_DF_PATH}/", suffix=".pkl")
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
    timestamped_df = get_timestamped_dataframe(df, definition.columns_definition)
    duration_added_df = get_duration_added_dataframe(timestamped_df, definition.columns_definition)
    transition_removed_df = get_transition_recognized_dataframe(duration_added_df, definition)
    numbered_df = get_numbered_dataframe(transition_removed_df, definition.columns_definition)
    bool_df = get_bool_dataframe(numbered_df, definition.columns_definition)
    outcome_and_treatment_dataframe = get_outcome_and_treatment_dataframe(bool_df, definition)
    renamed_df = get_renamed_dataframe(outcome_and_treatment_dataframe, definition.columns_definition)
    return renamed_df


def get_timestamped_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get timestamped dataframe, convert to Timestamp of pandas
    for k, v in columns_definition.items():
        if v in {ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP}:
            df = df.copy()
            df.loc[:, k] = pd.to_datetime(df[k], errors="coerce")
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
    groups[ColumnDefinition.DURATION] = (groups["max"] - groups["min"]).dt.total_seconds().astype(int)
    df = df.merge(groups[[ColumnDefinition.DURATION]], left_on=case_id_column, right_index=True)
    del groups
    return df


def get_duration_added_df_by_start_end_timestamp(df: DataFrame, case_id_column: str,
                                                 start_time_column: str, end_time_column: str) -> DataFrame:
    # Get duration added dataframe by start and end timestamp
    df = df.sort_values(by=[start_time_column, end_time_column])
    grouped = df.groupby(case_id_column).agg({start_time_column: "first", end_time_column: "last"})
    grouped[ColumnDefinition.DURATION] = grouped[end_time_column] - grouped[start_time_column]
    grouped[ColumnDefinition.DURATION] = grouped[ColumnDefinition.DURATION].dt.total_seconds().astype(int)
    df = df.merge(grouped[[ColumnDefinition.DURATION]], left_on=case_id_column, right_index=True)
    return df


def get_transition_recognized_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get transition recognized dataframe
    columns_definition = definition.columns_definition

    if not any(d == ColumnDefinition.TRANSITION for d in columns_definition.values()):
        return df

    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    start_transition = definition.start_transition
    end_transition = definition.end_transition
    value_counts = df[transition_column].value_counts()
    value_counts.index = value_counts.index.str.upper()

    if value_counts.get(start_transition, 0) == 0 and value_counts.get(end_transition, 0) == 0:
        return df
    elif value_counts.get(start_transition, 0) == 0:
        return df[df[transition_column].str.upper() == end_transition]
    elif value_counts.get(end_transition, 0) == 0:
        return df[df[transition_column].str.upper() == start_transition]
    elif definition.fast_mode:
        return df[df[transition_column].str.upper() == end_transition]
    else:
        df = df[df[transition_column].str.upper().isin([start_transition, end_transition])]
        return get_timestamped_dataframe_by_transition(df, definition)


def get_timestamped_dataframe_by_transition(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get timestamped dataframe by transition
    columns_definition = definition.columns_definition
    case_id_column = get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID)
    activity_column = get_defined_column_name(columns_definition, ColumnDefinition.ACTIVITY)
    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    timestamp_column = get_defined_column_name(columns_definition, ColumnDefinition.TIMESTAMP)
    start_transition = definition.start_transition
    end_transition = definition.end_transition

    df = df.sort_values([case_id_column, timestamp_column])
    df = df.reset_index(drop=True)

    event_df_list = []

    for case_id in df[case_id_column].unique():
        case_df = df[df[case_id_column] == case_id]
        events = {}
        pending_events = {}
        for i, row in case_df.iterrows():
            activity = row[activity_column]
            # Please note that not all activities must have start transition
            # Please note that the same kind of activity can occur multiple times in the same case
            if row[transition_column].upper() == start_transition.upper():
                # If activity has start transition, add to pending events
                pending_events[activity] = row
                pending_events[activity][ColumnDefinition.START_TIMESTAMP] = row[timestamp_column]
                pending_events[activity][ColumnDefinition.END_TIMESTAMP] = row[timestamp_column]
            elif row[transition_column].upper() == end_transition.upper():
                if activity in pending_events:
                    # If activity has start and end transition, get start time from pending events, then add to events
                    events[i] = pending_events.pop(activity)
                    events[i][ColumnDefinition.END_TIMESTAMP] = row[timestamp_column]
                else:
                    # If activity only has end transition, add to events directly
                    events[i] = row
                    events[i][ColumnDefinition.START_TIMESTAMP] = row[timestamp_column]
                    events[i][ColumnDefinition.END_TIMESTAMP] = row[timestamp_column]

        # Events to list
        events_list = list(events.values())
        pending_events_list = list(pending_events.values())
        events_list.extend(pending_events_list)

        # Turn events to dataframe
        events_df = pd.DataFrame(events_list)
        events_df = events_df.sort_values([ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP])
        events_df = events_df.reset_index(drop=True)
        event_df_list.append(events_df)

    df = pd.concat(event_df_list, ignore_index=True)
    df = df.drop(columns=[transition_column, timestamp_column])
    df = df.sort_values([case_id_column, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP])

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


def get_outcome_and_treatment_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get outcome and treatment dataframe
    case_id_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)
    outcome_definition = definition.outcome_definition
    treatment_definition = definition.treatment_definition

    if outcome_definition and treatment_definition:
        return get_labelled_dataframe_by_both(df, case_id_column, definition)
    elif outcome_definition:
        return get_labelled_dataframe_by_one(df, case_id_column, definition, by_outcome=True)
    elif treatment_definition:
        return get_labelled_dataframe_by_one(df, case_id_column, definition, by_outcome=False)

    result = df.groupby(case_id_column, group_keys=True).apply(lambda x: label_outcome_and_treatment(x, definition))
    result.columns = [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]
    result = result.reset_index(drop=True)
    df = df.merge(result, left_index=True, right_index=True)
    return df


def get_labelled_dataframe_by_both(df: DataFrame, case_id_column: str,
                                   definition: definition_schema.Definition) -> DataFrame:
    result = df.groupby(case_id_column, group_keys=True).apply(lambda x: label_outcome_and_treatment(x, definition))
    result.columns = [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]
    result = result.reset_index(drop=True)
    df = df.merge(result, left_index=True, right_index=True)
    return df


def get_labelled_dataframe_by_one(df: DataFrame, case_id_column: str, definition: definition_schema.Definition,
                                  by_outcome: bool = True) -> DataFrame:
    # Get labelled dataframe by one
    column_name = ColumnDefinition.OUTCOME if by_outcome else ColumnDefinition.TREATMENT
    df[column_name] = df.groupby(case_id_column).apply(
        lambda x: label_one_column(x, definition, by_outcome)
    ).reset_index(drop=True)
    return df


def label_outcome_and_treatment(group: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Label outcome and treatment
    outcome, treatment = get_labels(group, definition)
    outcome_label = pd.Series(1 if outcome else 0, index=group.index)
    treatment_label = pd.Series(1 if treatment else 0, index=group.index)
    return pd.concat([outcome_label, treatment_label], axis=1)


def label_one_column(group: DataFrame, definition: definition_schema.Definition, by_outcome: bool = True) -> Series:
    # Label on column
    label = get_label(group, definition, by_outcome)
    return pd.Series(1 if label else 0, index=group.index).reset_index(drop=True)


def get_labels(group: DataFrame, definition: definition_schema.Definition) -> tuple[bool, bool]:
    # Get labels
    columns_definition = definition.columns_definition
    outcome_column = get_defined_column_name(columns_definition, ColumnDefinition.OUTCOME)
    treatment_column = get_defined_column_name(columns_definition, ColumnDefinition.TREATMENT)

    if outcome_column:
        outcome = label_for_outcome(group[outcome_column].iloc[0])
    else:
        outcome = check_or_conditions(group, definition.outcome_definition, columns_definition)

    if treatment_column:
        treatment = label_for_treatment(group[treatment_column].iloc[0])
    else:
        treatment = check_or_conditions(group, definition.treatment_definition, columns_definition)

    return outcome, treatment


def get_label(group: DataFrame, definition: definition_schema.Definition, by_outcome: bool = True) -> bool:
    # Get label
    columns_definition = definition.columns_definition
    if by_outcome:
        outcome_column = get_defined_column_name(columns_definition, ColumnDefinition.OUTCOME)
        if outcome_column:
            return label_for_outcome(group[outcome_column].iloc[0])
        else:
            return check_or_conditions(group, definition.outcome_definition, columns_definition)
    else:
        treatment_column = get_defined_column_name(columns_definition, ColumnDefinition.TREATMENT)
        if not treatment_column:
            return label_for_treatment(group[treatment_column].iloc[0])
        else:
            return False


def label_for_outcome(data: str | int | float | bool) -> bool | None:
    # Label for outcome
    if isinstance(data, (int, float)):
        return int(data) > 0

    if isinstance(data, str):
        stripped_data = data.strip().lower()
        if stripped_data in {"true", "1", "yes", "y", "positive"}:
            return True
        elif any(stripped_data.startswith(pre) for pre in ["complete", "finish", "close", "success", "succeed"]):
            return True
        else:
            return False

    if isinstance(data, bool):
        return data

    return None


def label_for_treatment(data: str | int | float | bool) -> bool | None:
    # Label for treatment
    if isinstance(data, (int, float)):
        return int(data) > 0

    if isinstance(data, str):
        stripped_data = data.strip().lower()
        if stripped_data in {"true", "1", "yes", "y", "positive", "treatment", "treat", "treated"}:
            return True
        else:
            return False

    if isinstance(data, bool):
        return data

    return None


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
