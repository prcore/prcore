import logging

from pydantic import BaseModel

from blupee import glovar
from blupee.models.case import Case

# Enable logging
logger = logging.getLogger(__name__)


class Result(BaseModel):
    id: int
    date: int
    case: Case
    output: str = None

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.results)):
                if glovar.results[i].id == self.id:
                    glovar.results[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.results.append(self)
