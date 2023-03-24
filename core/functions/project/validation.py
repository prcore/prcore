import logging
from typing import Any

import pandas as pd
from fastapi import HTTPException

import core.models.project as project_model
from core.enums.definition import ColumnDefinition
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus
from core.schemas.definition import ProjectDefinition
from core.functions.common.etc import convert_to_seconds
from core.functions.definition.util import is_supported_operator

# Enable logging
logger = logging.getLogger(__name__)


def validate_project_definition(project_definition: list[list[ProjectDefinition]],
                                columns_definition: dict[str, ColumnDefinition]) -> None:
    # Check if the nested definition is valid
    if not isinstance(project_definition, list) or len(project_definition) < 1:
        raise HTTPException(status_code=400, detail="Invalid definition")

    for sub_list in project_definition:
        if not sub_list or not isinstance(sub_list, list) or len(sub_list) < 1:
            raise HTTPException(status_code=400, detail="Invalid definition")

        for unit_project_definition in sub_list:
            validate_unit_project_definition(unit_project_definition, columns_definition)


def validate_unit_project_definition(project_definition: ProjectDefinition,
                                     columns_definition: dict[str, ColumnDefinition]) -> None:
    column_definition = columns_definition.get(project_definition.column)

    if project_definition.column == ColumnDefinition.DURATION:
        column_definition = ColumnDefinition.DURATION

    if column_definition is None:
        raise HTTPException(status_code=400, detail=f"Column '{project_definition.column}' is not defined")

    if is_supported_operator(project_definition.operator, column_definition) is False:
        raise HTTPException(
            status_code=400,
            detail=(f"Operator '{project_definition.operator}' not supported "
                    f"for column '{project_definition.column}'")
        )

    validate_project_definition_value(project_definition.column, column_definition, project_definition.value)


def validate_project_definition_value(column: str, column_definition: ColumnDefinition, value: Any) -> None:
    # Check if the value is valid
    if column_definition == ColumnDefinition.NUMBER:
        try:
            float(value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"Invalid number value for {column}")

    if column_definition == ColumnDefinition.DATETIME:
        value_datetime = pd.to_datetime(value, errors="coerce")
        if pd.isnull(value_datetime):
            raise HTTPException(status_code=400, detail=f"Invalid datetime value for {column}")

    if column_definition == ColumnDefinition.CATEGORICAL:
        if not isinstance(value, str):
            raise HTTPException(status_code=400, detail=f"Invalid categorical value for {column},"
                                                        f"value must be a string")

    if column_definition == ColumnDefinition.DURATION:
        try:
            convert_to_seconds(value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid duration value for {column}")


def validate_project_status(db_project: project_model.Project) -> None:
    # Check if the project has a normal status
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)
    elif db_project.status == ProjectStatus.ERROR:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_ERROR)


def validate_streaming_status(db_project: project_model.Project, operation: str) -> None:
    # Check if the streaming or simulation status is valid
    validate_project_status(db_project)
    if operation == "start":
        if db_project.status == ProjectStatus.STREAMING:
            raise HTTPException(status_code=400, detail=ErrorType.STREAMING_STARTED)
        if db_project.status == ProjectStatus.SIMULATING:
            raise HTTPException(status_code=400, detail=ErrorType.SIMULATION_STARTED)
        if db_project.status != ProjectStatus.TRAINED:
            raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_TRAINED)
    elif operation == "stop":
        if db_project.status not in [ProjectStatus.STREAMING, ProjectStatus.SIMULATING]:
            raise HTTPException(status_code=400, detail=ErrorType.STREAMING_NOT_STARTED)


def validate_ongoing_dataset(columns: list[str], columns_definition: dict[str, ColumnDefinition],
                             case_attributes: list[str]) -> None:
    for column in columns_definition:
        if columns_definition.get(column) and column not in columns:
            raise ValueError(f"Column is defined but not in the new dataset: {column}")
    if case_attributes:
        for column in case_attributes:
            if column not in columns:
                raise ValueError(f"Case attribute is defined but not in the new dataset: {column}")
