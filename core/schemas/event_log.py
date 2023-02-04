import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class EventLogBase(BaseModel):
    file_name: str
    saved_name: str
    df_name: str | None = None


class EventLogCreate(EventLogBase):
    pass


class EventLog(EventLogBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
