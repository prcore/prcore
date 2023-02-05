import logging
from datetime import datetime

from pydantic import BaseModel

from core.responses.event_log import EventLogDto

# Enable logging
logger = logging.getLogger(__name__)


class ProjectDto(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    name: str
    description: str | None = None
    event_log: EventLogDto | None = None

    class Config:
        orm_mode = True


class AllProjectsResponse(BaseModel):
    message: str
    projects: list[ProjectDto] = []
