import logging

from pydantic import BaseModel

from core.schemas.definition import ProjectDefinition, Transition

# Enable logging
logger = logging.getLogger("prcore")


class CreateProjectRequest(BaseModel):
    event_log_id: int
    positive_outcome: list[list[ProjectDefinition]]
    treatment: list[list[ProjectDefinition]]
    fast_mode: bool = True
    start_transition: str = Transition.START
    end_transition: str = Transition.COMPLETE


class UpdateProjectRequest(BaseModel):
    positive_outcome: list[list[ProjectDefinition]]
    treatment: list[list[ProjectDefinition]]
    fast_mode: bool = True
    start_transition: str = Transition.START
    end_transition: str = Transition.COMPLETE


class BasicUpdateProjectRequest(BaseModel):
    name: str
    description: str = ""
