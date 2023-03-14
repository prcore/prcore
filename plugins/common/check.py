import logging
from typing import List, Dict, Any, Union

from pandas import DataFrame

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


def check_needed_columns(df: DataFrame, needed_columns: List[str]) -> bool:
    # Basic check according to the needed columns
    if (ColumnDefinition.CASE_ID not in df.columns
            or not get_timestamp_columns(df)
            or ColumnDefinition.ACTIVITY not in df.columns):
        return False

    # Check if all needed columns are in the df
    for column in needed_columns:
        if column in {ColumnDefinition.CASE_ID,
                      ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP,
                      ColumnDefinition.ACTIVITY}:
            continue
        if column not in df.columns:
            return False

    return True


def get_timestamp_columns(df: DataFrame) -> List[str]:
    if ColumnDefinition.TIMESTAMP in df.columns:
        return [ColumnDefinition.TIMESTAMP]
    elif ColumnDefinition.START_TIMESTAMP in df.columns and ColumnDefinition.END_TIMESTAMP in df.columns:
        return [ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP]
    else:
        return []


def check_column_classes(df: DataFrame, needed_columns: List[str]) -> str:
    # Check if the df has only two classes for outcome and treatment
    for column in {ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT}:
        if column in needed_columns and column in df.columns and df[column].nunique() < 2:
            return f"The {column} column must have two classes at least"
    return ""


def check_needed_info(additional_info: Dict[str, Any], needed_info: List[str]) -> Union[str, bool]:
    # Check if all needed information is in the additional_info
    for info in needed_info:
        if info not in additional_info:
            return False
    return True
