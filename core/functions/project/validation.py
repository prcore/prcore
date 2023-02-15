import logging

from fastapi import HTTPException

from core.enums.definition import ColumnDefinition
from core.schemas.definition import ProjectDefinition
from core.functions.definition.util import is_supported_operator

# Enable logging
logger = logging.getLogger("prcore")


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
