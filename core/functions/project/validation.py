import logging

from fastapi import HTTPException

from core.enums.definition import ColumnDefinition
from core.schemas.definition import ProjectDefinition
from core.functions.definition.util import get_supported_operators_by_column_name

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
            if project_definition.operator not in get_supported_operators_by_column_name(project_definition.column,
                                                                                         columns_definition):
                raise HTTPException(
                    status_code=400,
                    detail=(f"Operator '{project_definition.operator}' not supported "
                            f"for column '{project_definition.column}'")
                )

    return True
