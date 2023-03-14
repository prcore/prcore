import logging
from typing import Any

from pydantic import BaseModel

from core.schemas.definition import ProjectDefinition

# Enable logging
logger = logging.getLogger(__name__)


class CreateProjectRequest(BaseModel):
    event_log_id: int
    positive_outcome: list[list[ProjectDefinition]] | None = None
    treatment: list[list[ProjectDefinition]] | None = None
    parameters: dict[str, dict[str, Any]] = {}
    additional_info: dict[str, Any] = {}


class UpdateProjectRequest(BaseModel):
    positive_outcome: list[list[ProjectDefinition]] | None = None
    treatment: list[list[ProjectDefinition]] | None = None
    parameters: dict[str, dict[str, Any]] = {}
    additional_info: dict[str, Any] = {}


class BasicUpdateProjectRequest(BaseModel):
    name: str
    description: str = ""


class UploadOngoingDatasetRequest(BaseModel):
    additional_info: dict[str, Any] = {}


class StreamingOperationRequest(BaseModel):
    additional_info: dict[str, Any] = {}
