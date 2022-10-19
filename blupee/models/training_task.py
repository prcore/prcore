import logging

from pydantic import BaseModel

from blupee import glovar

# Enable logging
logger = logging.getLogger(__name__)


class TrainingTask(BaseModel):
    id: int
    status: str

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.training_tasks)):
                if glovar.training_tasks[i].id == self.id:
                    glovar.training_tasks[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.training_tasks.append(self)
