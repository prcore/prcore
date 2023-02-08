import logging

from fastapi import HTTPException

from core.enums.definition import ColumnDefinition, Operator, SupportedOperators

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


def get_defined_column_name(definition: dict[str, ColumnDefinition], wanted: ColumnDefinition) -> str:
    # Get activity column name
    result = ""

    try:
        result = [k for k, v in definition.items() if v == wanted]
        result = result[0] if len(result) > 0 else ""
    except Exception as e:
        logger.warning(f"Get defined column name error: {e}", exc_info=True)

    return result


def get_available_selections(definition: dict[str, ColumnDefinition], type_: str = "outcome") -> list[str]:
    # Get available selections
    result = []

    try:
        supported = [
            ColumnDefinition.TEXT,
            ColumnDefinition.NUMBER,
            ColumnDefinition.BOOLEAN,
            ColumnDefinition.DATETIME,
            ColumnDefinition.ACTIVITY,
            ColumnDefinition.RESOURCE,
            ColumnDefinition.DURATION,
            ColumnDefinition.COST,
            ColumnDefinition.TIMESTAMP,
            ColumnDefinition.START_TIMESTAMP,
            ColumnDefinition.END_TIMESTAMP
        ]
        result = [k for k, v in definition.items() if v in supported]

        if type_ != "outcome" or any(v == ColumnDefinition.DURATION for v in definition.values()):
            return result

        result.append(ColumnDefinition.DURATION.value)
    except Exception as e:
        logger.warning(f"Get available selections error: {e}", exc_info=True)

    return result
