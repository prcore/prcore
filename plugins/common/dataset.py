import logging
from multiprocessing import Pool, cpu_count
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pandas import DataFrame, read_pickle, read_csv
from sklearn.preprocessing import LabelBinarizer

from core.enums.dataset import EncodingType, OutcomeType
from core.enums.definition import ColumnDefinition
from core.functions.general.etc import get_processes_number

# Enable logging
logger = logging.getLogger(__name__)


def read_df_from_path(directory: str, df_name: str) -> DataFrame:
    try:
        return read_pickle(f"{directory}/{df_name}.pkl")
    except ValueError:
        # If the plugin's Python version is 3.6, then the pickle protocol is not compatible,
        # so we need to read the CSV file
        return read_csv(f"{directory}/{df_name}.csv")


def get_encoded_dfs_by_activity(original_df: DataFrame, encoding_type: EncodingType, outcome_type: OutcomeType,
                                include_treatment: bool, for_test: bool,
                                existing_data: Optional[Dict[str, Any]]) -> Tuple[Dict[int, DataFrame], Dict[str, Any]]:
    # Get encoded dataframes by activity for different lengths
    df = original_df.copy(deep=True)
    data = {}

    if existing_data is not None and "mapping" in existing_data:
        mapping = existing_data["mapping"]
        df = get_ordinal_encoded_df_by_given_mapping(df, ColumnDefinition.ACTIVITY, mapping)
        data["mapping"] = mapping
    elif encoding_type == EncodingType.SIMPLE_INDEX:
        df, mapping = get_ordinal_encoded_df_and_mapping(df, ColumnDefinition.ACTIVITY)
        data["mapping"] = mapping
    elif outcome_type == OutcomeType.LAST_ACTIVITY:
        _, mapping = get_ordinal_encoded_df_and_mapping(df, ColumnDefinition.ACTIVITY)
        data["mapping"] = mapping

    case_ids = df[ColumnDefinition.CASE_ID].values
    unique_case_ids = np.unique(case_ids)
    activities = df[ColumnDefinition.ACTIVITY].values
    data["grouped_activities"] = [activities[case_ids == case_id] for case_id in unique_case_ids]
    data["lengths"] = sorted({len(trace) for trace in data["grouped_activities"]})
    if ColumnDefinition.OUTCOME in df.columns:
        outcomes = df[ColumnDefinition.OUTCOME].values
        data["grouped_outcomes"] = [outcomes[case_ids == case_id][0] for case_id in unique_case_ids]
    if include_treatment and ColumnDefinition.TREATMENT in df.columns:
        treatments = df[ColumnDefinition.TREATMENT].values
        data["grouped_treatments"] = [treatments[case_ids == case_id][0] for case_id in unique_case_ids]
    if encoding_type in {EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED}:
        if existing_data is not None and "lb" in existing_data:
            lb = existing_data["lb"]
        else:
            lb = LabelBinarizer()
            lb = lb.fit(np.unique(activities))
        data["lb"] = lb

    processes_number = get_processes_number()
    lengths_split = np.array_split(data["lengths"], processes_number * 4)
    with Pool(processes=processes_number) as pool:
        results = pool.starmap(
            func=get_encoded_dataframes_by_activity_for_lengths,
            iterable=[(lengths, encoding_type, outcome_type, data, for_test) for lengths in lengths_split]
        )

    dataframes = {length: r for result in results for length, r in result.items()}

    return dataframes, data


def get_ordinal_encoded_df_and_mapping(original_df: DataFrame, column: str) -> Tuple[DataFrame, dict]:
    # Get ordinal encoded dataframe
    df = original_df.copy(deep=True)
    df[column] = df[column].astype("category")
    mapping = dict(enumerate(df[column].cat.categories))
    df[column] = df[column].cat.codes
    mapping = {v: k for k, v in mapping.items()}
    return df, mapping


def get_ordinal_encoded_df_by_given_mapping(original_df: DataFrame, column: str,
                                            mapping: Dict[Union[int, str], int]) -> DataFrame:
    # Get ordinal encoded dataframe
    df = original_df.copy(deep=True)
    df[column] = df[column].map(mapping)
    df = df.dropna(subset=[column])
    return df


def get_encoded_dataframes_by_activity_for_lengths(lengths: List[int], encoding_type: EncodingType,
                                                   outcome_type: OutcomeType,
                                                   data: Dict[str, Any], for_test: bool) -> Dict[int, DataFrame]:
    # Get encoded dataframes by activity for some lengths
    results = {}
    for length in lengths:
        if not for_test and len([group for group in data["grouped_activities"] if len(group) > length]) < 1000:
            continue
        if for_test:
            encoded_df = get_test_df_by_activity(length, encoding_type, data)
        else:
            encoded_df = get_training_df_by_activity(length, encoding_type, outcome_type, data)
        if encoded_df is None:
            continue
        results[length] = encoded_df
    return results


def get_test_df_by_activity(length: int, encoding_type: EncodingType, data: Dict[str, Any]) -> Optional[DataFrame]:
    test_data = []
    for i, group in enumerate(data["grouped_activities"]):
        if len(group) != length:
            continue
        x = get_data_array(group, length, encoding_type, data.get("lb"))
        if x is None:
            continue
        test_data.append([x])
    return get_test_df_from_data_list(test_data, length, encoding_type, data.get("lb"))


def get_data_array(group: np.array, length: int, encoding_type: EncodingType,
                   lb: Optional[LabelBinarizer]) -> Optional[np.ndarray]:
    # Get data array for a specific length
    x_raw = group[:length]
    if encoding_type == EncodingType.BOOLEAN and lb is not None:
        arr_encoded = lb.transform(x_raw)
        arr_sum = arr_encoded.sum(axis=0)
        x = np.where(arr_sum > 0, 1, 0)
    elif encoding_type == EncodingType.FREQUENCY_BASED and lb is not None:
        arr_encoded = lb.transform(x_raw)
        x = arr_encoded.sum(axis=0)
    elif encoding_type == EncodingType.SIMPLE_INDEX:
        x = group[:length]
    else:
        x = None
    return x


def get_test_df_from_data_list(test_data: List[List[Union[np.array, int]]], length: int, encoding_type: EncodingType,
                               lb: Optional[LabelBinarizer]) -> Optional[DataFrame]:
    if len(test_data) == 0:
        return None
    df = pd.DataFrame(data=test_data, columns=[ColumnDefinition.ACTIVITY])
    return get_activities_df(df, length, encoding_type, lb)


def get_activities_df(df: DataFrame, length: int, encoding_type: EncodingType,
                      lb: Optional[LabelBinarizer]) -> DataFrame:
    if encoding_type in {EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED} and lb is not None:
        activity_columns = lb.classes_
    else:
        activity_columns = [f"EVENT_{i}" for i in range(1, length + 1)]
    activities_df = pd.DataFrame(
        data=np.stack(df[ColumnDefinition.ACTIVITY], axis=0),
        columns=activity_columns
    )
    return activities_df


def get_training_df_by_activity(length: int, encoding_type: EncodingType, outcome_type: OutcomeType,
                                data: Dict[str, Any]) -> Optional[DataFrame]:
    training_data = []
    for i, group in enumerate(data["grouped_activities"]):
        if len(group) <= length:
            continue
        x = get_data_array(group, length, encoding_type, data.get("lb"))
        y = get_outcome_label_by_activity(group, data.get("grouped_outcomes"), length, i, outcome_type)
        t = get_treatment_label(data.get("grouped_treatments"), i)
        if x is None or y is None:
            continue
        if data.get("grouped_treatments") is not None:
            training_data.append([x, y, t])
        else:
            training_data.append([x, y])
    training_df = get_training_df_from_data_list(training_data, length, encoding_type, data.get("lb"))
    if (training_df is not None
            and encoding_type in {EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED}
            and outcome_type == OutcomeType.LAST_ACTIVITY):
        training_df = get_ordinal_encoded_df_by_given_mapping(training_df, ColumnDefinition.OUTCOME, data["mapping"])
    return training_df


def get_outcome_label_by_activity(activities: np.array, grouped_outcomes: Optional[List[int]], length: int, index: int,
                                  outcome_type: OutcomeType) -> Optional[int]:
    # Get outcome label for a specific index
    if outcome_type == OutcomeType.LABELLED and grouped_outcomes is not None:
        y = grouped_outcomes[index]
    elif outcome_type == OutcomeType.LAST_ACTIVITY:
        y = activities[length]
    else:
        y = None
    return y


def get_treatment_label(grouped_treatments: Optional[List[int]], index: int) -> Optional[int]:
    # Get treatment label for a specific index
    if grouped_treatments is not None:
        t = grouped_treatments[index]
    else:
        t = None
    return t


def get_training_df_from_data_list(training_data: List[List[Union[np.array, int]]], length: int,
                                   encoding_type: EncodingType, lb: Optional[LabelBinarizer]) -> Optional[DataFrame]:
    if len(training_data) == 0:
        return None

    if len(training_data[0]) == 2:
        columns = [ColumnDefinition.ACTIVITY, ColumnDefinition.OUTCOME]
    else:
        columns = [ColumnDefinition.ACTIVITY, ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]
    training_df = pd.DataFrame(data=training_data, columns=columns)

    activities_df = get_activities_df(training_df, length, encoding_type, lb)
    if len(training_data[0]) == 2:
        label_columns = [ColumnDefinition.OUTCOME]
    else:
        label_columns = [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]
    return pd.concat([activities_df, training_df[label_columns]], axis=1)


def get_boolean_encoding_dataframes_by_length(df: DataFrame) -> dict:
    # If one type of activity occurs in a trace, the corresponding column is set to 1, otherwise 0
    grouped_df = df.groupby(ColumnDefinition.CASE_ID)
    dataframes = {}
    all_activities = sorted(set(df[ColumnDefinition.ACTIVITY]))
    lengths_split = np.array_split(sorted(list(set([len(g) for _, g in grouped_df]))), cpu_count() * 4)

    with Pool(cpu_count()) as pool:
        results = pool.starmap(
            func=generate_boolean_encoded_dataframe_for_lengths,
            iterable=[(grouped_df, all_activities, lens) for lens in lengths_split]
        )

    for chunk in results:
        dataframes.update(chunk)

    return dataframes


def generate_boolean_encoded_dataframe_for_lengths(grouped_df: DataFrame, activities: list, lengths: list) -> dict:
    result = {}
    for length in lengths:
        r = get_boolean_encoded_sliced_groups(grouped_df, activities, length)
        if r is None:
            continue
        result[length] = r
    return result


def get_boolean_encoded_sliced_groups(grouped_df: DataFrame, activities: list, length: int) -> Optional[DataFrame]:
    sliced_groups = [get_boolean_encoded_df(group.iloc[:length], activities)
                     for _, group in grouped_df if len(group) >= length + 1]
    if len(sliced_groups) < 1000:
        return None
    return pd.concat(sliced_groups, ignore_index=True)


def get_boolean_encoded_df(group: DataFrame, activities: list) -> DataFrame:
    data = {}
    for activity in activities:
        data[f"{ColumnDefinition.ACTIVITY}_{activity}"] = 1 if activity in set(group[ColumnDefinition.ACTIVITY]) else 0
    for label in [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]:
        if label in group:
            data[label] = group.iloc[0][label]
    return pd.DataFrame([data])
