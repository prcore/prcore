import logging
from datetime import datetime

from pydantic import BaseModel
from core.schemas.definition import Definition

# Enable logging
logger = logging.getLogger("prcore")


class EventLogBase(BaseModel):
    file_name: str


class EventLogCreate(EventLogBase):
    saved_name: str
    df_name: str | None = None
    training_df_name: str | None = None
    simulation_df_name: str | None = None


class EventLog(EventLogBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    definition: Definition | None = None

    class Config:
        orm_mode = True
