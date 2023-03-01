import logging

from pydantic import BaseModel

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


class ProjectResultCaseResponse(BaseModel):
    prescriptions: list[dict]
    events: list[list]


class ProjectResultResponse(BaseModel):
    message: str
    cases_count: int
    columns: list[str]
    columns_definition: list[str]
    cases: dict[str, ProjectResultCaseResponse]


class SimulateProjectResponse(BaseModel):
    message: str
    project_id: int

