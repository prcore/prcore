import logging
from typing import List

from pandas import Timestamp
from pydantic import BaseModel

from core.schemas.event_log import EventLog
from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


class AllEventLogsResponse(BaseModel):
    message: str
    event_logs: List[EventLog] = []


class UploadEventLogResponse(BaseModel):
    message: str
    event_log_id: int
    events_brief: list[list[str | ColumnDefinition | Timestamp | None]]
