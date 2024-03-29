import logging
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame

from core.enums.definition import ColumnDefinition, Operator, SupportedOperators
from core.functions.common.etc import convert_to_seconds
from core.functions.definition.util import get_supported_operators
from core.schemas.definition import ProjectDefinition

# Enable logging
logger = logging.getLogger(__name__)


def check_or_conditions(group: DataFrame, conditions: list[list[ProjectDefinition]],
                        columns_definition: dict[str, ColumnDefinition],
                        resource_column: str) -> tuple[bool, str | None]:
    # Check if the data of the row satisfies the OR conditions
    if conditions is None or len(conditions) == 0:
        return False, None

    for condition in conditions:
        result, treatment_resource = check_and_conditions(group, condition, columns_definition, resource_column)
        if result:
            return True, treatment_resource

    return False, None


def check_and_conditions(group: DataFrame, conditions: list[ProjectDefinition],
                         columns_definition: dict[str, ColumnDefinition],
                         resource_column: str) -> tuple[bool, str | None]:
    # Check if the data of the row satisfies the AND conditions
    if len(conditions) == 0:
        return False, None

    mask = np.ones(len(group), dtype=bool)
    for condition in conditions:
        mask &= check_atomic_condition(group, condition, columns_definition)

    row_indices = np.flatnonzero(mask)
    if len(row_indices) > 0 and resource_column:
        row_index = row_indices[0]  # Get the index of the first row that meets the conditions
        treatment_resource = group.iloc[row_index][resource_column]
        return True, treatment_resource
    elif len(row_indices) > 0:
        return True, None

    return False, None


def check_atomic_condition(group: DataFrame, condition: ProjectDefinition,
                           columns_definition: dict[str, ColumnDefinition]) -> pd.Series:
    # Check if the data of the row satisfies the condition
    column_name = condition.column
    column_definition = columns_definition.get(condition.column)
    if condition.column == ColumnDefinition.DURATION:
        column_definition = ColumnDefinition.DURATION
    operator = condition.operator
    threshold = condition.value
    supported_operators = get_supported_operators(column_definition)

    if operator not in supported_operators:
        raise ValueError(f"Operator '{operator}' not supported for column '{condition.column}'")

    if supported_operators == SupportedOperators.TEXT:
        return compare_text(group, column_name, operator, threshold)
    elif supported_operators == SupportedOperators.NUMBER:
        return compare_number(group, column_name, columns_definition, operator, threshold)
    elif supported_operators == SupportedOperators.DATETIME:
        return compare_datetime(group, column_name, operator, threshold)
    elif supported_operators == SupportedOperators.BOOLEAN:
        return compare_boolean(group, column_name, operator)
    elif supported_operators == SupportedOperators.CATEGORICAL:
        return compare_categorical(group, column_name, threshold)

    return pd.Series([False] * len(group), index=group.index)


def compare_text(group: DataFrame, column_name: str, operator: Operator, threshold: Any) -> pd.Series:
    # Compare text
    threshold = str(threshold).lower()
    if operator == Operator.EQUAL:
        return group[column_name].str.lower() == threshold
    elif operator == Operator.NOT_EQUAL:
        return group[column_name].str.lower() != threshold
    elif operator == Operator.CONTAINS:
        return group[column_name].str.lower().str.contains(threshold)
    elif operator == Operator.NOT_CONTAINS:
        return ~group[column_name].str.lower().str.contains(threshold)
    return pd.Series([False] * len(group), index=group.index)


def compare_number(group: DataFrame, column_name: str, columns_definition: dict[str, ColumnDefinition],
                   operator: Operator, threshold: Any) -> pd.Series:
    # Compare number
    if columns_definition.get(column_name, column_name) == ColumnDefinition.DURATION:
        threshold = convert_to_seconds(threshold)
    else:
        threshold = pd.to_numeric(threshold, errors="coerce")
    if threshold < 0 or np.isnan(threshold):
        raise ValueError("Invalid threshold")
    threshold: float | int

    if operator == Operator.EQUAL:
        return group[column_name] == threshold
    elif operator == Operator.NOT_EQUAL:
        return group[column_name].values != threshold
    elif operator == Operator.LESS_THAN:
        return group[column_name].values < threshold
    elif operator == Operator.LESS_THAN_OR_EQUAL:
        return group[column_name].values <= threshold
    elif operator == Operator.GREATER_THAN:
        return group[column_name].values > threshold
    elif operator == Operator.GREATER_THAN_OR_EQUAL:
        return group[column_name].values >= threshold
    return pd.Series([False] * len(group), index=group.index)


def compare_boolean(group: DataFrame, column_name: str, operator: Operator) -> pd.Series:
    # Compare boolean
    if operator == Operator.IS_TRUE:
        return group[column_name]
    elif operator == Operator.IS_FALSE:
        return ~group[column_name]
    return pd.Series([False] * len(group), index=group.index)


def compare_datetime(group: DataFrame, column_name: str, operator: Operator, threshold: Any) -> pd.Series:
    # Compare datetime
    threshold = pd.to_datetime(threshold, errors="coerce")
    if pd.isnull(threshold):
        raise ValueError("Invalid threshold")

    # If the column is timestamp, and not in the group, then it is the start timestamp
    # This is because the timestamp column is removed during the transition recognize process
    if column_name == ColumnDefinition.TIMESTAMP and column_name not in group.columns:
        column_name = ColumnDefinition.START_TIMESTAMP

    first_timestamp = group[column_name].iloc[0]
    if first_timestamp.tzinfo is not None and threshold.tzinfo is None:
        threshold = threshold.replace(tzinfo=first_timestamp.tzinfo)
    elif first_timestamp.tzinfo is None and threshold.tzinfo is not None:
        group[column_name] = group[column_name].dt.tz_localize(threshold.tzinfo)

    if operator == Operator.EQUAL:
        return group[column_name] == threshold
    elif operator == Operator.NOT_EQUAL:
        return group[column_name] != threshold
    elif operator == Operator.EARLIER_THAN:
        return group[column_name] < threshold
    elif operator == Operator.EARLIER_THAN_OR_EQUAL:
        return group[column_name] <= threshold
    elif operator == Operator.LATER_THAN:
        return group[column_name] > threshold
    elif operator == Operator.LESS_THAN_OR_EQUAL:
        return group[column_name] >= threshold
    return pd.Series([False] * len(group), index=group.index)


def compare_categorical(group: DataFrame, column_name: str, threshold: Any) -> pd.Series:
    # Compare categorical
    threshold = str(threshold).lower()
    return group[column_name].str.lower() == threshold
