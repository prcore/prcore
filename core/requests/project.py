import logging
from datetime import datetime

from pandas import Timestamp
from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class CreateProjectRequest(BaseModel):
    event_log_id: int
    positive_outcome: list[list[dict[str, datetime | int | float | str | bool | None]]]
    treatment: list[list[dict[str, datetime | int | float | str | bool | None]]]
