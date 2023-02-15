import logging

from core.enums.definition import ColumnDefinition, DefinitionType, Operator, SupportedOperators

# Enable logging
logger = logging.getLogger("prcore")


def is_supported_operator(operator: Operator, column_definition: ColumnDefinition) -> bool:
    # Check if the operator is supported by the column definition
    supported_operators = get_supported_operators(column_definition)
    return operator in supported_operators if supported_operators is not None else False


def get_supported_operators(column_definition: ColumnDefinition) -> SupportedOperators | None:
    # Get supported operators
    if column_definition in DefinitionType.TEXT:
        return SupportedOperators.TEXT
    elif column_definition in DefinitionType.NUMBER:
        return SupportedOperators.NUMBER
    elif column_definition in DefinitionType.BOOLEAN:
        return SupportedOperators.BOOLEAN
    elif column_definition in DefinitionType.DATETIME:
        return SupportedOperators.DATETIME
    return None


def get_defined_column_name(definition: dict[str, ColumnDefinition], wanted: ColumnDefinition) -> str:
    # Get activity column name
    result = ""

    try:
        result = [k for k, v in definition.items() if v == wanted]
        result = result[0] if len(result) > 0 else ""
    except Exception as e:
        logger.warning(f"Get defined column name error: {e}", exc_info=True)

    return result


def get_available_options(definition: dict[str, ColumnDefinition], type_: str = "outcome") -> list[str]:
    # Get available options
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

        result.append(ColumnDefinition.DURATION)
    except Exception as e:
        logger.warning(f"Get available options error: {e}", exc_info=True)

    return result


def get_start_timestamp(columns_definition: dict[str, ColumnDefinition]) -> str:
    # Get start timestamp column name
    return (get_defined_column_name(columns_definition, ColumnDefinition.TIMESTAMP)
            or get_defined_column_name(columns_definition, ColumnDefinition.START_TIMESTAMP))
