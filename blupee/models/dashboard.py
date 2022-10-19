import logging

from pydantic import BaseModel

from blupee import glovar
from blupee.models.event_log import PreviousEventLog, CurrentEventLog

# Enable logging
logger = logging.getLogger(__name__)


class Dashboard(BaseModel):
    id: int
    name: str
    description: str = ""
    previous_event_log: PreviousEventLog
    current_event_log: CurrentEventLog

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.dashboards)):
                if glovar.dashboards[i].id == self.id:
                    glovar.dashboards[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.dashboards.append(self)
