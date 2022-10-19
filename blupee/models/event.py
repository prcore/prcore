import logging

from pydantic import BaseModel

from blupee import glovar

# Enable logging
logger = logging.getLogger(__name__)


class Event(BaseModel):
    id: int
    activity: str
    timestamp: str
    resource: str
    attributes: dict

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.events)):
                if glovar.events[i].id == self.id:
                    glovar.events[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.events.append(self)
