import logging

from fastapi import HTTPException

import core.models.project as project_model
from core.enums.definition import ColumnDefinition
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus
from core.schemas.definition import ProjectDefinition
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


def validate_streaming_status(db_project: project_model.Project, operation: str) -> bool:
    # Check if the streaming or simulation status is valid
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)

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

    return True
