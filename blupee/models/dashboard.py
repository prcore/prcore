import logging
from typing import List

from pydantic import BaseModel

from blupee import glovar
from blupee.models.event_log import PreviousEventLog, CurrentEventLog
from blupee.models.training_task import TrainingTask
from blupee.models.prescribing_task import PrescribingTask


# Enable logging
logger = logging.getLogger(__name__)


class Dashboard(BaseModel):
    id: int
    name: str
    description: str = ""
    previous_event_log: PreviousEventLog
    current_event_log: CurrentEventLog
    algorithms: list
    training_tasks: List[TrainingTask]
    prescribing_tasks: List[PrescribingTask]

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.dashboards)):
                if glovar.dashboards[i].id == self.id:
                    glovar.dashboards[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.dashboards.append(self)
