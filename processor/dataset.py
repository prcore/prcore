from multiprocessing import Pool

import numpy as np
import pandas as pd
from pandas import DataFrame

import core.schemas.definition as definition_schema
from core.enums.definition import ColumnDefinition, DefinitionType
from core.functions.common.dataset import (get_timestamped_dataframe, get_transition_recognized_dataframe,
                                           get_renamed_dataframe)
from core.functions.common.etc import get_processes_number
from core.functions.definition.util import get_defined_column_name
from processor.condition import check_or_conditions


def get_processed_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get processed dataframe
    timestamped_df = get_timestamped_dataframe(df, definition.columns_definition)
    duration_added_df = get_duration_added_dataframe(timestamped_df, definition.columns_definition)
    transition_removed_df = get_transition_recognized_dataframe_detailed_mode(duration_added_df, definition)
    numbered_df = get_numbered_dataframe(transition_removed_df, definition.columns_definition)
    bool_df = get_bool_dataframe(numbered_df, definition.columns_definition)
    outcome_and_treatment_dataframe = get_outcome_and_treatment_dataframe(bool_df, definition)
    renamed_df = get_renamed_dataframe(outcome_and_treatment_dataframe, definition.columns_definition,
                                       definition.case_attributes)
    return renamed_df


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


def get_transition_recognized_dataframe_detailed_mode(df: DataFrame,
                                                      definition: definition_schema.Definition) -> DataFrame:
    # Get transition recognized dataframe in detailed mode
    result_df = get_transition_recognized_dataframe(df, definition)
    if result_df is not None:
        return result_df
    columns_definition = definition.columns_definition
    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    start_transition = definition.start_transition
    complete_transition = definition.complete_transition
    abort_transition = definition.abort_transition
    df = df[df[transition_column].str.upper().isin([start_transition, complete_transition, abort_transition])]
    return process_df_parallel(get_timestamped_dataframe_by_transition, df, definition, (definition,))


def get_timestamped_dataframe_by_transition(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get timestamped dataframe by transition
    columns_definition = definition.columns_definition
    case_id_column = get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID)
    activity_column = get_defined_column_name(columns_definition, ColumnDefinition.ACTIVITY)
    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    timestamp_column = get_defined_column_name(columns_definition, ColumnDefinition.TIMESTAMP)
    start_transition = definition.start_transition
    complete_transition = definition.complete_transition
    abort_transition = definition.abort_transition

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
            elif row[transition_column].upper() in [complete_transition, abort_transition]:
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
    if not definition.outcome_definition and not definition.treatment_definition:
        return df
    return process_df_parallel(get_labelled_dataframe, df, definition, (definition,))


def get_labelled_dataframe(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Get labelled dataframe
    case_id_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)
    outcome_definition = definition.outcome_definition
    outcome_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.OUTCOME)
    treatment_definition = definition.treatment_definition
    treatment_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.TREATMENT)
    resource_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.RESOURCE)

    df = df.reset_index(drop=True)
    result = df.groupby(case_id_column, group_keys=True).apply(lambda x: label_outcome_and_treatment(x, definition))
    result.columns = [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT, ColumnDefinition.TREATMENT_RESOURCE]
    result = result.reset_index(drop=True)

    if not outcome_definition and not outcome_column:
        result = result.drop(columns=[ColumnDefinition.OUTCOME])
    if not treatment_definition and not treatment_column:
        result = result.drop(columns=[ColumnDefinition.TREATMENT])
    if not treatment_definition or treatment_column or not resource_column:
        result = result.drop(columns=[ColumnDefinition.TREATMENT_RESOURCE])

    df = df.merge(result, left_index=True, right_index=True)
    return df


def label_outcome_and_treatment(group: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Label outcome and treatment, and get resource
    outcome, treatment, resource = get_labels(group, definition)
    outcome_reverse = definition.outcome_definition_negative
    if outcome_reverse:
        outcome = not outcome
    outcome_label = pd.Series(1 if outcome else 0, index=group.index)
    treatment_label = pd.Series(1 if treatment else 0, index=group.index)
    resource = pd.Series(resource, index=group.index, dtype="object")
    return pd.concat([outcome_label, treatment_label, resource], axis=1)


def get_labels(group: DataFrame, definition: definition_schema.Definition) -> tuple[bool, bool, str]:
    # Get labels
    columns_definition = definition.columns_definition
    outcome_column = get_defined_column_name(columns_definition, ColumnDefinition.OUTCOME)
    treatment_column = get_defined_column_name(columns_definition, ColumnDefinition.TREATMENT)
    resource_column = get_defined_column_name(columns_definition, ColumnDefinition.RESOURCE)
    resource = None

    if outcome_column:
        outcome = label_for_outcome(group[outcome_column].iloc[0])
    else:
        outcome, _ = check_or_conditions(group, definition.outcome_definition, columns_definition, "")

    if treatment_column:
        treatment = label_for_treatment(group[treatment_column].iloc[0])
    else:
        treatment, resource = check_or_conditions(group, definition.treatment_definition, columns_definition,
                                                  resource_column)

    return outcome, treatment, resource


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


def process_df_parallel(target: callable, df: DataFrame, definition: definition_schema.Definition,
                        args: tuple) -> DataFrame:
    # Process dataframe parallel
    case_id_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)
    processes_number = get_processes_number()
    unique_cases = df[case_id_column].unique()
    case_splits = np.array_split(unique_cases, processes_number)
    df_splits = [df[df[case_id_column].isin(case_split)] for case_split in case_splits if len(case_split) > 0]

    with Pool(processes_number) as pool:
        results = pool.starmap(target, [(df_split,) + args for df_split in df_splits])

    result_df = pd.concat(results)
    return result_df
