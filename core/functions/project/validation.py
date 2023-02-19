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
                                columns_definition: dict[str, ColumnDefinition]) -> bool:
    # Check if the nested definition is valid
    if not project_definition or not isinstance(project_definition, list) or len(project_definition) < 1:
        raise HTTPException(status_code=400, detail="Invalid definition")

    for sub_list in project_definition:
        if not sub_list or not isinstance(sub_list, list) or len(sub_list) < 1:
            raise HTTPException(status_code=400, detail="Invalid definition")

        for project_definition in sub_list:
            column_definition = columns_definition.get(project_definition.column)

            if column_definition is None and project_definition.column != ColumnDefinition.DURATION:
                raise HTTPException(status_code=400, detail=f"Column '{project_definition.column}' is not defined")

            if is_supported_operator(project_definition.operator, column_definition) is False:
                raise HTTPException(
                    status_code=400,
                    detail=(f"Operator '{project_definition.operator}' not supported "
                            f"for column '{project_definition.column}'")
                )

    return True


def validate_simulation_status(db_project: project_model.Project, operation: str) -> bool:
    # Check if the simulation is finished
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)
    if db_project.status == ProjectStatus.ACTIVATING:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_ACTIVATING)

    if operation == "start":
        if db_project.status == ProjectStatus.SIMULATING:
            raise HTTPException(status_code=400, detail=ErrorType.SIMULATION_STARTED)
        if db_project.status != ProjectStatus.TRAINED:
            raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_TRAINED)
    elif operation == "stop" and db_project.status != ProjectStatus.SIMULATING:
        raise HTTPException(status_code=400, detail=ErrorType.SIMULATION_NOT_STARTED)

    return True
