import logging
from typing import Union

from pydantic import BaseModel

from blupee import glovar

# Enable logging
logger = logging.getLogger(__name__)


class Result(BaseModel):
    id: int
    date: int
    type: str
    output: Union[bool, str, dict] = None
    model: dict = {}

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.results)):
                if glovar.results[i].id == self.id:
                    glovar.results[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.results.append(self)
