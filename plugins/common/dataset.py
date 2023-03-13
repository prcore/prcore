import logging
from multiprocessing import Pool, cpu_count
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


def get_one_hot_dataframes_by_length(df: DataFrame) -> dict:
    grouped_df = df.groupby(ColumnDefinition.CASE_ID)
    dataframes = {}
    all_activities = sorted(set(df[ColumnDefinition.ACTIVITY]))
    lengths_split = np.array_split(sorted(list(set([len(g) for _, g in grouped_df]))), cpu_count() * 4)

    with Pool(16) as pool:
        results = pool.starmap(
            func=generate_dataframe_for_lengths,
            iterable=[(grouped_df, all_activities, lens) for lens in lengths_split]
        )

    for chunk in results:
        dataframes.update(chunk)

    return dataframes


def generate_dataframe_for_lengths(grouped_df: DataFrame, activities: list, lengths: list) -> dict:
    result = {}
    for length in lengths:
        r = get_sliced_groups(grouped_df, activities, length)
        if r is None:
            continue
        result[length] = r
    return result


def get_sliced_groups(grouped_df: DataFrame, activities: list, length: int) -> Optional[DataFrame]:
    sliced_groups = [get_one_hot_encoded_df(group.iloc[:length], activities)
                     for _, group in grouped_df if len(group) >= length + 1]
    if len(sliced_groups) < 1000:
        return None
    return pd.concat(sliced_groups, ignore_index=True)


def get_one_hot_encoded_df(group: DataFrame, activities: list) -> DataFrame:
    data = {}
    for activity in activities:
        data[f"{ColumnDefinition.ACTIVITY}_{activity}"] = 1 if activity in set(group[ColumnDefinition.ACTIVITY]) else 0
    for label in [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]:
        if label in group:
            data[label] = group.iloc[0][label]
    return pd.DataFrame([data])
