import logging

from fastapi import HTTPException
from pandas import DataFrame

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


def validate_columns_definition(columns_definition: dict[str, ColumnDefinition | None], df: DataFrame) -> bool:
    # Check if the column definition is valid
    if any(column not in df.columns.tolist() for column in columns_definition.keys()):
        raise HTTPException(status_code=400, detail="Invalid column definition")

    if not any(d == ColumnDefinition.CASE_ID for d in columns_definition.values()):
        raise HTTPException(status_code=400, detail="No case ID column found")
    if list(columns_definition.values()).count(ColumnDefinition.CASE_ID) > 1:
        raise HTTPException(status_code=400, detail="Multiple case ID columns found")

    if not any(d == ColumnDefinition.ACTIVITY for d in columns_definition.values()):
        raise HTTPException(status_code=400, detail="No activity column found")
    if list(columns_definition.values()).count(ColumnDefinition.ACTIVITY) > 1:
        raise HTTPException(status_code=400, detail="Multiple activity columns found")

    if (not (has_timestamp := any(d == ColumnDefinition.TIMESTAMP for d in columns_definition.values()))
            and not any(d == ColumnDefinition.START_TIMESTAMP for d in columns_definition.values())
            and not any(d == ColumnDefinition.END_TIMESTAMP for d in columns_definition.values())):
        raise HTTPException(status_code=400, detail="No timestamp column found")
    if list(columns_definition.values()).count(ColumnDefinition.TIMESTAMP) > 1:
        raise HTTPException(status_code=400, detail="Multiple timestamp columns found")
    if list(columns_definition.values()).count(ColumnDefinition.START_TIMESTAMP) > 1:
        raise HTTPException(status_code=400, detail="Multiple start timestamp columns found")
    if list(columns_definition.values()).count(ColumnDefinition.END_TIMESTAMP) > 1:
        raise HTTPException(status_code=400, detail="Multiple end timestamp columns found")

    if not has_timestamp and not all(d in columns_definition.values()
                                     for d in [ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP]):
        raise HTTPException(status_code=400, detail="Invalid column definition")

    return True


def validate_case_attributes(case_attributes: list[str] | None, df: DataFrame) -> bool:
    # Check if the case attributes are valid
    if case_attributes and any(attribute not in df.columns.tolist() for attribute in case_attributes):
        raise HTTPException(status_code=400, detail="Invalid case attributes")

    return True
