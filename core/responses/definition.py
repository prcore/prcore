import logging
from datetime import datetime

from pandas import Timestamp
from pydantic import BaseModel

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


class DefinitionDto(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    columns_definition: dict[str, ColumnDefinition]
    outcome_definition: list[list[dict[str, datetime | int | float | str | bool | None]]] | None = None
    treatment_definition: list[list[dict[str, datetime | int | float | str | bool | None]]] | None = None

    class Config:
        orm_mode = True
