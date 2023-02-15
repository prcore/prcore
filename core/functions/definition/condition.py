import logging
import re
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame

from core.enums.definition import ColumnDefinition, Operator, SupportedOperators
from core.functions.definition.util import get_supported_operators
from core.schemas.definition import ProjectDefinition

# Enable logging
logger = logging.getLogger(__name__)


def check_or_conditions(group: DataFrame, conditions: list[list[ProjectDefinition]],
                        columns_definition: dict[str, ColumnDefinition]) -> bool:
    # Check if the data of the row satisfies the OR conditions
    if len(conditions) == 0:
        return False

    for condition in conditions:
        if check_and_conditions(group, condition, columns_definition):
            return True
    return False


def check_and_conditions(group: DataFrame, conditions: list[ProjectDefinition],
                         columns_definition: dict[str, ColumnDefinition]) -> bool:
    # Check if the data of the row satisfies the AND conditions
    if len(conditions) == 0:
        return False

    for condition in conditions:
        if not check_atomic_condition(group, condition, columns_definition):
            return False
    return True


def check_atomic_condition(group: DataFrame, condition: ProjectDefinition,
                           columns_definition: dict[str, ColumnDefinition]) -> bool:
    # Check if the data of the row satisfies the condition
    column_name = condition.column
    column_definition = columns_definition.get(condition.column)
    operator = condition.operator
    threshold = condition.value
    supported_operators = get_supported_operators(column_definition)

    if supported_operators is None:
        raise ValueError("Cannot find supported operators")

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

    return False


def compare_text(group: DataFrame, column_name: str, operator: Operator, threshold: Any) -> bool:
    # Compare text
    threshold = str(threshold).lower()
    if operator == Operator.EQUAL:
        return np.any(group[column_name].str.lower() == threshold)
    elif operator == Operator.NOT_EQUAL:
        return np.any(group[column_name].str.lower() != threshold)
    elif operator == Operator.CONTAINS:
        return np.any(threshold in group[column_name].str.lower())
    elif operator == Operator.NOT_CONTAINS:
        return np.any(threshold not in group[column_name].str.lower())
    return False


def compare_number(group: DataFrame, column_name: str, columns_definition: dict[str, ColumnDefinition],
                   operator: Operator, threshold: Any) -> bool:
    # Compare number
    if columns_definition.get(column_name, column_name) == ColumnDefinition.DURATION:
        threshold = convert_to_seconds(threshold)
    else:
        threshold = pd.to_numeric(threshold, errors="coerce")
    if threshold < 0 or np.isnan(threshold):
        raise ValueError("Invalid threshold")
    if operator == Operator.EQUAL:
        return np.any(group[column_name] == threshold)
    elif operator == Operator.NOT_EQUAL:
        return np.any(group[column_name] != threshold)
    elif operator == Operator.LESS_THAN:
        return np.any(group[column_name] < threshold)
    elif operator == Operator.LESS_THAN_OR_EQUAL:
        return np.any(group[column_name] <= threshold)
    elif operator == Operator.GREATER_THAN:
        return np.any(group[column_name] > threshold)
    elif operator == Operator.GREATER_THAN_OR_EQUAL:
        return np.any(group[column_name] >= threshold)
    return False


def compare_boolean(group: DataFrame, column_name: str, operator: Operator) -> bool:
    # Compare boolean
    if operator == Operator.IS_TRUE:
        return np.any(group[column_name])
    elif operator == Operator.IS_FALSE:
        return np.any(~group[column_name])
    return False


def compare_datetime(group: DataFrame, column_name: str, operator: Operator, threshold: Any) -> bool:
    # Compare datetime
    threshold = pd.to_datetime(threshold, errors="coerce")
    if np.isnan(threshold):
        raise ValueError("Invalid threshold")

    # If the column is timestamp, and not in the group, then it is the start timestamp
    # This is because the timestamp column is removed during the transition recognize process
    if column_name == ColumnDefinition.TIMESTAMP and column_name not in group.columns:
        column_name = ColumnDefinition.START_TIMESTAMP

    if operator == Operator.EQUAL:
        return np.any(group[column_name] == threshold)
    elif operator == Operator.NOT_EQUAL:
        return np.any(group[column_name] != threshold)
    elif operator == Operator.EARLIER_THAN:
        return np.any(group[column_name] < threshold)
    elif operator == Operator.EARLIER_THAN_OR_EQUAL:
        return np.any(group[column_name] <= threshold)
    elif operator == Operator.LATER_THAN:
        return np.any(group[column_name] > threshold)
    elif operator == Operator.LESS_THAN_OR_EQUAL:
        return np.any(group[column_name] >= threshold)
    return False


def convert_to_seconds(time_str):
    time_str = str(time_str).strip().lower()
    if time_str.isdigit():
        return int(time_str)

    match = re.match(r"^(\d+)\s*(\w+)$", time_str)
    if not match:
        raise ValueError("Invalid input")

    value = int(match.group(1))
    unit = match.group(2)

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
