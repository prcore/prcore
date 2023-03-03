import logging

from pydantic import BaseModel

from core.enums.definition import ColumnDefinition
from core.schemas.project import Project

# Enable logging
logger = logging.getLogger(__name__)


class AllProjectsResponse(BaseModel):
    message: str
    projects: list[Project] = []


class ProjectResponse(BaseModel):
    message: str
    project: Project


class CreateProjectResponse(BaseModel):
    message: str
    project: Project


class DatasetUploadResponse(BaseModel):
    message: str
    project_id: int
    result_key: str


class DatasetResultCaseResponse(BaseModel):
    prescriptions: list[dict]
    events: list[list]


class DatasetResultResponse(BaseModel):
    message: str
    project_status: str
    finished_plugins: list[str]
    cases_count: int | None = None
    columns: list[str] | None = None
    columns_definition: dict[str, ColumnDefinition] | None = None
    cases: dict[str, DatasetResultCaseResponse] | None = None


class SimulateProjectResponse(BaseModel):
    message: str
    project_id: int
