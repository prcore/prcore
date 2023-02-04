import logging
from datetime import datetime

from pydantic import BaseModel

from core.models.event_log import EventLog

# Enable logging
logger = logging.getLogger(__name__)


class Project(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    description: str = ""
    event_log: EventLog
