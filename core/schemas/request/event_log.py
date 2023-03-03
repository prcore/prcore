import logging

from pydantic import BaseModel

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


class ColumnsDefinitionRequest(BaseModel):
    columns_definition: dict[str, ColumnDefinition | None]
    case_attributes: list[str] | None = None
