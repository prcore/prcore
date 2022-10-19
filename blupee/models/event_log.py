import logging

from pydantic import BaseModel

from blupee import glovar

# Enable logging
logger = logging.getLogger(__name__)


class EventLog(BaseModel):
    id: int
    name: str
    path: str
    data: dict


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
