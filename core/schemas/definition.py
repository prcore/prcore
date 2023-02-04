import logging
from datetime import datetime

from pydantic import BaseModel
from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


class DefinitionBase(BaseModel):
    columns_definition: dict[str, ColumnDefinition | None]
    outcome_definition: list[list[dict[str, datetime | int | str]]] | None = None
    treatment_definition: list[list[dict[str, datetime | int | str]]] | None = None


class DefinitionCreate(DefinitionBase):
    pass


class Definition(DefinitionBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
