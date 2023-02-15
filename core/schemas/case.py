import logging
from datetime import datetime

from pydantic import BaseModel

from core.schemas.event import Event

# Enable logging
logger = logging.getLogger("prcore")


class CaseBase(BaseModel):
    project_id: int
    case_id: str
    completed: bool = False


class CaseCreate(CaseBase):
    pass


class Case(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    events: list[Event] = []

    class Config:
        orm_mode = True
