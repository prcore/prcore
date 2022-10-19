import logging

from pydantic import BaseModel

from blupee import glovar
from blupee.models.event import Event

# Enable logging
logger = logging.getLogger(__name__)


class Case(BaseModel):
    id: int
    status: str
    events: list[Event] = []

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.cases)):
                if glovar.cases[i].id == self.id:
                    glovar.cases[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.cases.append(self)
