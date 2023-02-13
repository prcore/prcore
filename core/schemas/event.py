import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class EventBase(BaseModel):
    project_id: int
    attributes: dict[str, str | bool | int | float | None] = {}
    prescriptions: dict[str, Any] = {}
    prescribed: bool = False
    sent: bool = False


class EventCreate(EventBase):
    pass


class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
