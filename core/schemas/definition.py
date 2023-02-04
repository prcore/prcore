import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class DefinitionBase(BaseModel):
    columns_definition: dict[str, str]
    outcome_definition: list[list[dict[str, datetime | int | str]]]
    treatment_definition: list[list[dict[str, datetime | int | str]]]


class DefinitionCreate(DefinitionBase):
    pass


class Definition(DefinitionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
