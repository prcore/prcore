import logging
from datetime import datetime

from pydantic import BaseModel
from core.enums.definition import ColumnDefinition, Operator

# Enable logging
logger = logging.getLogger(__name__)


class ProjectDefinition(BaseModel):
    column: str
    operator: Operator
    value: datetime | int | float | str | bool | None = None


class DefinitionBase(BaseModel):
    columns_definition: dict[str, ColumnDefinition | None]
    outcome_definition: list[list[ProjectDefinition]] | None = None
    treatment_definition: list[list[ProjectDefinition]] | None = None


class DefinitionCreate(DefinitionBase):
    pass


class Definition(DefinitionBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
