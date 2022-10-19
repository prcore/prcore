import logging
from typing import Any

from pydantic import BaseModel

from blupee import glovar
from blupee.models.case import Case

# Enable logging
logger = logging.getLogger(__name__)


class PrescribingTask(BaseModel):
    id: int
    status: str
    case: Case
    algorithms: list
    result: Any = None

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.prescribing_tasks)):
                if glovar.prescribing_tasks[i].id == self.id:
                    glovar.prescribing_tasks[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.prescribing_tasks.append(self)
