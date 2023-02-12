import logging
import re
from typing import Any

from pandas import Timestamp

from core.enums.definition import ColumnDefinition, Operator, SupportedOperators
from core.functions.definition.util import get_supported_operators
from core.schemas.definition import ProjectDefinition

# Enable logging
logger = logging.getLogger(__name__)


def check_atomic_condition(value: Timestamp | bool | int | float | str, condition: ProjectDefinition,
                           columns_definition: dict[str, ColumnDefinition]) -> bool:
    # Check if the data of the row satisfies the condition
    column_definition = columns_definition.get(condition.column)
    operator = condition.operator
    threshold = condition.value
    supported_operators = get_supported_operators(column_definition)

    if supported_operators is None:
        raise ValueError("Cannot find supported operators")

    if operator not in supported_operators:
        raise ValueError(f"Operator '{operator}' not supported for column '{condition.column}'")

    if supported_operators == SupportedOperators.TEXT:
        return compare_text(value, operator, threshold)
    elif supported_operators == SupportedOperators.NUMBER:
        return False


def compare_text(value: Any, operator: Operator, threshold: Any) -> bool:
    # Compare text
    if operator == Operator.EQUAL:
        return value == threshold
    elif operator == Operator.NOT_EQUAL:
        return value != threshold
    elif operator == Operator.CONTAINS:
        return threshold in value
    elif operator == Operator.NOT_CONTAINS:
        return threshold not in value
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
