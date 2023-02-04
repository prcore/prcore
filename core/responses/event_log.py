import logging
from typing import List

from pydantic import BaseModel

from core.schemas.event_log import EventLog

# Enable logging
logger = logging.getLogger(__name__)


class AllEventLogsResponse(BaseModel):
    message: str
    event_logs: List[EventLog] = []
