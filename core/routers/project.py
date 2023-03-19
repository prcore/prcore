import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, UploadFile
from fastapi_pagination import Page
from sqlalchemy.orm import Session

import core.schemas.request.project as project_request
import core.schemas.response.project as project_response
import core.schemas.project as project_schema
from core.functions.common.request import get_real_ip, get_db
from core.security.token import validate_token
from core.services.project import (process_project_creation, process_projects_reading, process_project_reading,
                                   process_project_update, process_project_definition_update, process_project_deletion,
                                   process_ongoing_dataset_uploading, process_ongoing_dataset_result,
                                   process_stream_starting, process_stream_stopping, process_stream_clearing,
                                   process_stream_result, process_dataset_downloading)


# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/project")


@router.post("", response_model=project_response.CreateProjectResponse)
def create_project(request: Request, create_body: project_request.CreateProjectRequest,
                   db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Create project for event log {create_body and create_body.event_log_id} - "
                   f"from IP {get_real_ip(request)}")
    return process_project_creation(create_body, db)


@router.get("/all", response_model=Page[project_schema.Project])
def read_projects(request: Request, db: Session = Depends(get_db),
                  _: bool = Depends(validate_token)):
    logger.warning(f"Read projects - from IP {get_real_ip(request)}")
    return process_projects_reading(db)


@router.get("/{project_id}", response_model=project_response.ProjectResponse)
async def read_project(request: Request, project_id: int, db: Session = Depends(get_db),
                       _: bool = Depends(validate_token)):
    logger.warning(f"Read project {project_id} - from IP {get_real_ip(request)}")
    return process_project_reading(project_id, db)


@router.put("/{project_id}", response_model=project_response.ProjectResponse)
def update_project(request: Request, project_id: int, update_body: project_request.BasicUpdateProjectRequest,
                   db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update project {project_id} - from IP {get_real_ip(request)}")
    return process_project_update(project_id, update_body, db)


@router.put("/{project_id}/definition", response_model=project_response.CreateProjectResponse)
def update_project_definition(request: Request, project_id: int, update_body: project_request.UpdateProjectRequest,
                              db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update project definition for {project_id} - from IP {get_real_ip(request)}")
    return process_project_definition_update(project_id, update_body, db)


@router.delete("/{project_id}", response_model=project_response.DeleteProjectResponse)
def delete_project(request: Request, project_id: int, db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Delete project {project_id} - from IP {get_real_ip(request)}")
    return process_project_deletion(project_id, db)


@router.post("/{project_id}/result", response_model=project_response.DatasetUploadResponse)
def upload_ongoing_dataset(request: Request, project_id: int, background_tasks: BackgroundTasks,
                           file: UploadFile = Form(), seperator: str = Form(","),
                           db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Upload ongoing dataset to project {project_id} - from IP {get_real_ip(request)}")
    return process_ongoing_dataset_uploading(project_id, background_tasks, file, seperator, db)


@router.get("/{project_id}/result/{result_key}", response_model=project_response.DatasetResultResponse)
def get_ongoing_dataset_result(request: Request, project_id: int, result_key: str, background_tasks: BackgroundTasks,
                               db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Get ongoing dataset result of project {project_id} - from IP {get_real_ip(request)}")
    return process_ongoing_dataset_result(project_id, result_key, background_tasks, db)


@router.put("/{project_id}/stream/start", response_model=project_response.StreamProjectResponse)
@router.put("/{project_id}/stream/start/{streaming_type}", response_model=project_response.StreamProjectResponse)
def streaming_start(request: Request, project_id: int, streaming_type: str = "streaming",
                    db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Enable streaming mode <{streaming_type}> for project {project_id} - "
                   f"from IP {get_real_ip(request)}")
    return process_stream_starting(project_id, streaming_type, db)


@router.put("/{project_id}/stream/stop", response_model=project_response.StreamProjectResponse)
def streaming_stop(request: Request, project_id: int, db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Disable streaming mode for project {project_id} - from IP {get_real_ip(request)}")
    return process_stream_stopping(project_id, db)


@router.put("/{project_id}/stream/clear", response_model=project_response.StreamProjectResponse)
def stream_clear(request: Request, project_id: int, db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Clear stream data of project {project_id} - from IP {get_real_ip(request)}")
    return process_stream_clearing(project_id, db)


@router.get("/{project_id}/stream/result")
async def streaming_result(request: Request, project_id: int, db: Session = Depends(get_db),
                           _: bool = Depends(validate_token)):
    logger.warning(f"Read streaming result of project {project_id} - from IP {get_real_ip(request)}")
    return await process_stream_result(request, project_id, db)


@router.get("/{project_id}/dataset/{dataset_type}")
def download_project_dataset(request: Request, project_id: int, dataset_type: str, background_tasks: BackgroundTasks,
                             db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Download dataset <{dataset_type}> of project {project_id} - from IP {get_real_ip(request)}")
    return process_dataset_downloading(project_id, dataset_type, background_tasks, db)
