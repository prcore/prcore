import logging
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
