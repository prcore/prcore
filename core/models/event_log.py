import logging
from datetime import datetime

from pydantic import BaseModel

from core import glovar
from core.models.case import Case
from core.models.definition import Definition
from core.models.event import Event

# Enable logging
logger = logging.getLogger(__name__)


class EventLog(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    file_name: str
    saved_name: str
    df_name: str
    definition: Definition
    cases: list[Case]
    events: list[Event]


class PreviousEventLog(EventLog):
    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.previous_event_logs)):
                if glovar.previous_event_logs[i].id == self.id:
                    glovar.previous_event_logs[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.previous_event_logs.append(self)


class CurrentEventLog(EventLog):
    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.current_event_logs)):
                if glovar.current_event_logs[i].id == self.id:
                    glovar.current_event_logs[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.current_event_logs.append(self)
