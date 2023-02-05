import logging
from datetime import datetime

from pydantic import BaseModel
from core.schemas.event_log import EventLog

# Enable logging
logger = logging.getLogger(__name__)


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    event_log: EventLog | None = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
