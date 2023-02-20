import logging

from pydantic import BaseModel

from core.schemas.definition import ProjectDefinition, Transition

# Enable logging
logger = logging.getLogger(__name__)


class CreateProjectRequest(BaseModel):
    event_log_id: int
    positive_outcome: list[list[ProjectDefinition]] | None = None
    treatment: list[list[ProjectDefinition]] | None = None
    fast_mode: bool = True
    start_transition: str = Transition.START
    complete_transition: str = Transition.COMPLETE
    abort_transition: str = Transition.ATE_ABORT


class UpdateProjectRequest(BaseModel):
    positive_outcome: list[list[ProjectDefinition]] | None = None
    treatment: list[list[ProjectDefinition]] | None = None
    fast_mode: bool = True
    start_transition: str = Transition.START
    complete_transition: str = Transition.COMPLETE
    abort_transition: str = Transition.ATE_ABORT


class BasicUpdateProjectRequest(BaseModel):
    name: str
    description: str = ""
