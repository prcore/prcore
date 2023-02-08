import logging

from pydantic import BaseModel

from core.schemas.project import Project

# Enable logging
logger = logging.getLogger(__name__)


class AllProjectsResponse(BaseModel):
    message: str
    projects: list[Project] = []


class CreateProjectResponse(BaseModel):
    message: str
    project: Project
