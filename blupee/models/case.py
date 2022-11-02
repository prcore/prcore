import logging

from pydantic import BaseModel

from blupee import glovar
from blupee.models.event import Event
from blupee.models.identifier import get_identifier
from blupee.models.result import Result

# Enable logging
logger = logging.getLogger(__name__)


class Case(BaseModel):
    id: int
    status: str
    events: list[Event] = []
    results: list[Result] = []

    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.cases)):
                if glovar.cases[i].id == self.id:
                    glovar.cases[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.cases.append(self)

    def get_predicted_result(self):
        if self.status == "closed":
            return None
        if not self.results:
            return None
        return self.results[-1]

    def get_latest_two_events(self):
        if len(self.events) < 2:
            return None
        return self.events[-2:]

    def get_current_event_activity(self):
        if not self.events:
            return None
        return self.events[-1].activity

    def add_predicted_result(self, result):
        self.results.append(result)
        self.save()

    def predict_next_event(self, algorithms):
        for algorithm in algorithms:
            predicted_result = algorithm.predict(self.events)

            if not predicted_result:
                return

            new_result = Result(
                id=get_identifier(),
                date=predicted_result["date"],
                type=predicted_result["type"],
                current=self.get_current_event_activity(),
                output=predicted_result["output"],
                given_by=predicted_result["algorithm"]
            )
            new_result.save()
            self.add_predicted_result(new_result)
