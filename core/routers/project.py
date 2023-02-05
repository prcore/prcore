import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as event_log_crud
import core.crud.project as project_crud
import core.models.project as project_model
import core.responses.project as project_response
import core.schemas.project as project_schema
from core.database import get_db
from core.security.token import validate_token

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/project")


@router.post("", response_model=project_response.CreateProjectResponse)
async def create_project(request: Request, db: Session = Depends(get_db),
                         _: bool = Depends(validate_token)):
    logger.warning(f"Create project - from IP {request.client.host}")
    request_body = await request.json()
    db_event_log = event_log_crud.get_event_log(db, request_body.get("event_log_id"))

    if not db_event_log:
        raise HTTPException(status_code=400, detail="No valid event log provided")

    db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)

    if db_project:
        raise HTTPException(status_code=400, detail="Project already exists for this event log")

    db_project = project_crud.create_project(
        db=db,
        project=project_schema.ProjectCreate(name=db_event_log.file_name),
        event_log_id=db_event_log.id
    )

    return {
        "message": "Project created successfully",
        "project": db_project
    }


@router.get("/all", response_model=project_response.AllProjectsResponse)
def read_projects(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                      _: bool = Depends(validate_token)):
    logger.warning(f"Read projects - from IP {request.client.host}")
    return {
        "message": "Projects retrieved successfully",
        "projects": project_crud.get_projects(db, skip=skip, limit=limit)
    }
