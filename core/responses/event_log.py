import logging

from pandas import Timestamp
from pydantic import BaseModel

from core.enums.definition import ColumnDefinition
from core.schemas.event_log import EventLog

# Enable logging
logger = logging.getLogger(__name__)


class AllEventLogsResponse(BaseModel):
    message: str
    event_logs: list[EventLog] = []


class UploadEventLogResponse(BaseModel):
    message: str
    event_log_id: int
    columns_header: list[str]
    columns_inferred_definition: list[ColumnDefinition | None]
    columns_data: list[list[str | Timestamp | None]]


class UpdateEventLogResponse(BaseModel):
    message: str
    event_log_id: int
    received_definition: dict[str, ColumnDefinition]
    activities_count: dict[str, int]
    outcome_selections: list[str]
    treatment_selections: list[str]
