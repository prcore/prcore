import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class EventLogBase(BaseModel):
    file_name: str
    saved_name: str
    df_name: str


class EventLogCreate(EventLogBase):
    pass


class EventLog(EventLogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
