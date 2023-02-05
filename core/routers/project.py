import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

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


@router.get("/all", response_model=project_response.AllProjectsResponse)
def read_projects(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                      _: bool = Depends(validate_token)):
    logger.warning(f"Read projects - from IP {request.client.host}")
    return {
        "message": "Projects retrieved successfully",
        "projects": project_crud.get_projects(db, skip=skip, limit=limit)
    }
