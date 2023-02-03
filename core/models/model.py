import logging

from pydantic import BaseModel

from core import glovar

# Enable logging
logger = logging.getLogger(__name__)


class Model(BaseModel):
    id: int
    status: str

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.models)):
                if glovar.models[i].id == self.id:
                    glovar.models[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.models.append(self)
