import logging
from typing import Any

from fastapi import HTTPException

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


def validate_columns(request_body: Any, columns_definition: dict[str, ColumnDefinition],
                     case_attributes: list[str]) -> None:
    for column in columns_definition:
        if column not in request_body:
            raise HTTPException(status_code=400, detail=f"Missing pre-defined column {column}")
    if case_attributes:
        for column in case_attributes:
            if column not in request_body:
                raise HTTPException(status_code=400, detail=f"Missing case attribute {column}")
