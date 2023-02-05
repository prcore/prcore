import logging

from fastapi import HTTPException

from core.enums.definition import ColumnDefinition, Operator, SupportedOperators
from core.schemas.definition import ProjectDefinition

# Enable logging
logger = logging.getLogger(__name__)


def get_supported_operators_by_column_name(column_name: str, columns_definition: dict[str, ColumnDefinition]) -> list[Operator]:
    # Get column definition
    column_definition = get_column_definition(column_name, columns_definition)

    # Get supported operators
    return get_supported_operators(column_definition)


def get_column_definition(column_name: str, columns_definition: dict[str, ColumnDefinition]) -> ColumnDefinition:
    # Get column definition
    column_definition = columns_definition.get(column_name)

    if column_definition is None:
        raise HTTPException(status_code=400, detail=f"Column '{column_name}' is not defined")

    return column_definition


def get_supported_operators(column_definition: ColumnDefinition) -> list[Operator]:
    # Get supported operators
    if column_definition in {ColumnDefinition.TEXT, ColumnDefinition.ACTIVITY, ColumnDefinition.RESOURCE}:
        return SupportedOperators.TEXT.value
    if column_definition in {ColumnDefinition.NUMBER, ColumnDefinition.DURATION, ColumnDefinition.COST}:
        return SupportedOperators.NUMBER.value
    if column_definition in {ColumnDefinition.BOOLEAN}:
        return SupportedOperators.BOOLEAN.value
    if column_definition in {ColumnDefinition.DATETIME, ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP,
                             ColumnDefinition.END_TIMESTAMP}:
        return SupportedOperators.DATETIME.value
