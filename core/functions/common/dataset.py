import logging
from typing import Optional

import pandas as pd
from pandas import DataFrame

from core.enums.definition import ColumnDefinition, DefinitionType
from core.functions.definition.util import get_defined_column_name, get_column_definition
from core.schemas import definition as definition_schema

# Enable logging
logger = logging.getLogger(__name__)


def get_timestamped_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Get timestamped dataframe, convert to Timestamp of pandas
    for k, v in columns_definition.items():
        if v in DefinitionType.DATETIME:
            df = df.copy()
            df.loc[:, k] = pd.to_datetime(df[k], errors="coerce")
    return df


def get_transition_recognized_dataframe(df: DataFrame, definition: definition_schema.Definition) -> Optional[DataFrame]:
    # Get transition recognized dataframe
    columns_definition = definition.columns_definition

    if not any(d == ColumnDefinition.TRANSITION for d in columns_definition.values()):
        return df

    transition_column = get_defined_column_name(columns_definition, ColumnDefinition.TRANSITION)
    start_transition = definition.start_transition
    complete_transition = definition.complete_transition
    abort_transition = definition.abort_transition
    value_counts = df[transition_column].value_counts()
    value_counts.index = value_counts.index.str.upper()

    if value_counts.get(start_transition, 0) == 0 and value_counts.get(complete_transition, 0) == 0:
        return df
    elif value_counts.get(start_transition, 0) == 0:
        return df[df[transition_column].str.upper() == complete_transition]
    elif value_counts.get(complete_transition, 0) == 0:
        return df[df[transition_column].str.upper() == start_transition]
    elif definition.fast_mode:
        return df[df[transition_column].str.upper().isin([complete_transition, abort_transition])]
    else:
        return None


def get_renamed_dataframe(df: DataFrame, columns_definition: dict[str, ColumnDefinition],
                          case_attributes: list[str]) -> DataFrame:
    # Get renamed dataframe
    columns_need_to_rename = {}
    for column in df.columns.tolist():
        definition = get_column_definition(column, columns_definition)
        if definition in DefinitionType.SPECIAL:
            columns_need_to_rename[column] = definition
        elif definition == ColumnDefinition.CATEGORICAL:
            columns_need_to_rename[column] = f"CATEGORICAL_{column}"
        elif case_attributes and column in case_attributes:
            columns_need_to_rename[column] = f"CASE_ATTRIBUTE_{definition}_{column}"
        else:
            columns_need_to_rename[column] = f"EVENT_ATTRIBUTE_{definition}_{column}"
    df = df.rename(columns=columns_need_to_rename)
    return df
