import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy_future import paginate
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

import core.crud.case as case_crud
import core.crud.definition as definition_crud
import core.crud.event as event_crud
import core.crud.event_log as event_log_crud
import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
import core.models.project as project_model
import core.schemas.request.project as project_request
import core.schemas.response.project as project_response
import core.schemas.definition as definition_schema
import core.schemas.project as project_schema
from core.confs import path
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus, ProjectStatusGroup, PluginStatus
from core.functions.plugin.util import enhance_additional_infos, get_active_plugins
from core.functions.event_log.dataset import (get_ongoing_dataset_path, get_original_dataset_path,
                                              get_processed_dataset_path, get_simulation_dataset_path)
from core.functions.event_log.job import start_pre_processing
from core.functions.general.etc import process_daemon
from core.functions.general.file import delete_file, get_extension
from core.functions.general.request import get_real_ip, get_db
from core.functions.message.sender import send_streaming_prepare_to_all_plugins
from core.functions.project.prescribe import (delete_result_from_memory, get_ongoing_dataset_result_key,
                                              process_ongoing_dataset, run_project_watcher_for_ongoing_dataset)
from core.functions.project.streaming import event_generator, disable_streaming
from core.functions.project.validation import (validate_project_definition, validate_project_status,
                                               validate_streaming_status)
from core.starters import memory
from core.starters.database import engine
from core.security.token import validate_token

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/project")


@router.post("", response_model=project_response.CreateProjectResponse)
def create_project(request: Request, create_body: project_request.CreateProjectRequest,
                   db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Create project for event log {create_body and create_body.event_log_id} - "
                   f"from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_event_log = event_log_crud.get_event_log(db, create_body.event_log_id)
    if not db_event_log:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_NOT_FOUND)
    elif not db_event_log.definition or not db_event_log.definition.columns_definition:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_DEFINITION_NOT_FOUND)
    db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)
    if db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_EXISTED)

    # Validate the user's input
    columns_definition = db_event_log.definition.columns_definition
    positive_outcome = create_body.positive_outcome
    treatment = create_body.treatment
    positive_outcome and validate_project_definition(positive_outcome, columns_definition)
    treatment and validate_project_definition(treatment, columns_definition)

    # Create the project
    definition_crud.set_project_level_definition(
        db=db,
        db_definition=db_event_log.definition,
        outcome=create_body.positive_outcome,
        treatment=create_body.treatment
    )
    db_project = project_crud.create_project(
        db=db,
        project=project_schema.ProjectCreate(name=db_event_log.file_name),
        event_log_id=db_event_log.id
    )

    # Check if the project is created with a test file
    if (test := memory.log_tests.get(db_event_log.id)) is not None:
        _file = test["file"]
        separator = test["separator"]
        extension = test["extension"]
        result_key = get_ongoing_dataset_result_key(_file, extension, separator, db_project)
        memory.log_tests.pop(db_event_log.id)
    else:
        result_key = None

    # Start the pre-processing
    engine.dispose()
    process_daemon(
        target=start_pre_processing,
        args=(db_project.id, get_active_plugins(), create_body.parameters, create_body.additional_info),
        threaded=True
    )

    # Start the test file watching
    result_key and run_project_watcher_for_ongoing_dataset(db_project.id, result_key)

    return {
        "message": "Project created successfully",
        "project": db_project,
        "result_key": result_key
    }


@router.get("/all", response_model=Page[project_schema.Project])
def read_projects(request: Request, db: Session = Depends(get_db),
                  _: bool = Depends(validate_token)):
    logger.warning(f"Read projects - from IP {get_real_ip(request)}")
    return paginate(db, select(project_model.Project).order_by(desc(project_model.Project.created_at)))  # type: ignore


@router.get("/{project_id}", response_model=project_response.ProjectResponse)
async def read_project(request: Request, project_id: int, db: Session = Depends(get_db),
                       _: bool = Depends(validate_token)):
    logger.warning(f"Read project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)

    return {
        "message": "Project retrieved successfully",
        "project": db_project
    }


@router.put("/{project_id}", response_model=project_response.ProjectResponse)
def update_project(request: Request, project_id: int, update_body: project_request.BasicUpdateProjectRequest,
                   db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)

    # Set name or description
    db_project = project_crud.update_name_and_description(db, db_project, update_body.name, update_body.description)

    return {
        "message": "Project's basic information updated successfully",
        "project": db_project
    }


@router.put("/{project_id}/definition", response_model=project_response.CreateProjectResponse)
def update_project_definition(request: Request, project_id: int,
                              update_body: project_request.UpdateProjectRequest,
                              db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update project definition for {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)
    elif db_project.status not in {ProjectStatus.WAITING, ProjectStatus.TRAINED, ProjectStatus.STREAMING,
                                   ProjectStatus.SIMULATING, ProjectStatus.ERROR}:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_READY)
    db_event_log = event_log_crud.get_event_log(db, db_project.event_log_id)
    if not db_event_log:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_NOT_FOUND)

    # Validate the user's input
    columns_definition = db_event_log.definition.columns_definition
    positive_outcome = update_body.positive_outcome
    treatment = update_body.treatment
    positive_outcome and validate_project_definition(positive_outcome, columns_definition)
    treatment and validate_project_definition(treatment, columns_definition)
    disable_streaming(db, db_project, True)

    # Update the project
    definition_crud.set_project_level_definition(
        db=db,
        db_definition=db_event_log.definition,
        outcome=update_body.positive_outcome,
        treatment=update_body.treatment
    )

    # Start the pre-processing
    project_crud.update_status(db, db_project, ProjectStatus.PREPROCESSING)
    engine.dispose()
    process_daemon(
        target=start_pre_processing,
        args=(db_project.id, get_active_plugins(), update_body.parameters, update_body.additional_info, True),
        threaded=True
    )

    return {
        "message": "Project definition updated successfully",
        "project": db_project
    }


@router.delete("/{project_id}", response_model=project_response.DeleteProjectResponse)
def delete_project(request: Request, project_id: int,
                   db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Delete project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)

    # Stop streaming
    disable_streaming(db, db_project)

    # Delete all the project's data
    plugin_crud.delete_all_plugins_by_project_id(db, project_id)
    event_crud.delete_all_events_by_project_id(db, project_id)
    case_crud.delete_all_cases_by_project_id(db, project_id)
    event_log_id = db_project.event_log.id
    definition_id = db_project.event_log.definition.id
    project_crud.delete_project(db, db_project)
    event_log_crud.delete_event_log_by_id(db, event_log_id)
    definition_crud.delete_definition_by_id(db, definition_id)

    return {
        "message": "Project deleted successfully",
        "project_id": project_id
    }


@router.post("/{project_id}/result", response_model=project_response.DatasetUploadResponse)
def upload_ongoing_dataset(request: Request, project_id: int, background_tasks: BackgroundTasks,
                           file: UploadFile = Form(), seperator: str = Form(","),
                           db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Upload ongoing dataset to project {project_id} - from IP {get_real_ip(request)}")

    if not file or not file.file or (extension := get_extension(file.filename)) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    db_project = project_crud.get_project_by_id(db, project_id)
    validate_project_status(db_project)
    if db_project.status not in {ProjectStatus.TRAINED, ProjectStatus.STREAMING, ProjectStatus.SIMULATING}:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_READY)

    result_key = get_ongoing_dataset_result_key(file.file, extension, seperator, db_project)
    if not result_key:
        raise HTTPException(status_code=400, detail=ErrorType.PROCESS_DATASET_ERROR)

    background_tasks.add_task(process_ongoing_dataset, result_key)
    return {
        "message": "Ongoing dataset uploaded successfully",
        "project_id": project_id,
        "result_key": result_key
    }


@router.get("/{project_id}/result/{result_key}", response_model=project_response.DatasetResultResponse)
def get_ongoing_dataset_result(request: Request, project_id: int, result_key: str, background_tasks: BackgroundTasks,
                               db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Get ongoing dataset result of project {project_id} - from IP {get_real_ip(request)}")

    db_project = project_crud.get_project_by_id(db, project_id)
    validate_project_status(db_project)

    if result_key not in memory.ongoing_results or db_project.id != memory.ongoing_results[result_key]["project_id"]:
        raise HTTPException(status_code=404, detail=ErrorType.RESULT_NOT_FOUND)

    result = memory.ongoing_results[result_key]
    if not len(result["plugins"]) or len(result["results"]) != len(result["plugins"]):
        return {
            "message": "Ongoing dataset result is still processing",
            "project_status": db_project.status,
            "expected_plugins": list(result["plugins"].keys()),
            "finished_plugins": list(result["results"].keys()),
        }

    logger.warning("Start to merge the result")
    for plugin_result in result["results"].values():
        for case_id, case_result in plugin_result.items():
            result["cases"][case_id]["prescriptions"].append(case_result)
    logger.warning("Merge the result successfully")

    background_tasks.add_task(delete_result_from_memory, result_key)
    return {
        "message": "Ongoing dataset result retrieved successfully",
        "project_status": db_project.status,
        "expected_plugins": list(result["plugins"].keys()),
        "finished_plugins": list(result["results"].keys()),
        "cases_count": result["cases_count"],
        "columns": result["columns"],
        "columns_definition": result["columns_definition"],
        "case_attributes": result["case_attributes"],
        "cases": result["cases"]
    }


@router.put("/{project_id}/stream/start", response_model=project_response.StreamProjectResponse)
@router.put("/{project_id}/stream/start/{streaming_type}", response_model=project_response.StreamProjectResponse)
def streaming_start(request: Request, project_id: int, streaming_type: str = "streaming",
                    db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Enable streaming mode <{streaming_type}> for project {project_id} - "
                   f"from IP {get_real_ip(request)}")

    # Extract the wanted project status
    try:
        project_status = ProjectStatus(streaming_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=ErrorType.INVALID_STREAMING_TYPE)

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    validate_streaming_status(db_project, "start")

    # Start the streaming
    db_project = project_crud.update_status(db, db_project, project_status)
    plugins = {plugin.key: plugin.id for plugin in db_project.plugins
               if plugin.status in {PluginStatus.TRAINED, PluginStatus.STREAMING}}
    model_names = {plugin.id: plugin.model_name for plugin in db_project.plugins}
    additional_infos = enhance_additional_infos(
        additional_infos={plugin.key: plugin.additional_info for plugin in db_project.plugins},
        active_plugins=get_active_plugins(),
        definition=definition_schema.Definition.from_orm(db_project.event_log.definition)
    )
    send_streaming_prepare_to_all_plugins(plugins, db_project.id, model_names, additional_infos)
    return {
        "message": "Project streaming started successfully",
        "project_id": project_id
    }


@router.put("/{project_id}/stream/stop", response_model=project_response.StreamProjectResponse)
def streaming_stop(request: Request, project_id: int, db: Session = Depends(get_db),
                   _: bool = Depends(validate_token)):
    logger.warning(f"Disable streaming mode for project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    validate_streaming_status(db_project, "stop")

    # Stop the streaming
    disable_streaming(db, db_project)

    return {
        "message": "Project streaming stopped successfully",
        "project_id": project_id
    }


@router.put("/{project_id}/stream/clear", response_model=project_response.StreamProjectResponse)
def stream_clear(request: Request, project_id: int, db: Session = Depends(get_db),
                 _: bool = Depends(validate_token)):
    logger.warning(f"Clear stream data of project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    validate_project_status(db_project)

    # Stop the simulation
    disable_streaming(db, db_project)

    # Remove all the cases and events belonging to the project
    event_crud.delete_all_events_by_project_id(db, db_project.id)
    case_crud.delete_all_cases_by_project_id(db, db_project.id)

    return {
        "message": "Project stream data is cleared successfully",
        "project_id": project_id
    }


@router.get("/{project_id}/stream/result")
async def streaming_result(request: Request, project_id: int, db: Session = Depends(get_db),
                           _: bool = Depends(validate_token)):
    logger.warning(f"Read streaming result of project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    validate_project_status(db_project)

    # Check if the project is streaming
    streaming_project = memory.streaming_projects.get(project_id)
    enabled = streaming_project and not streaming_project["finished"].is_set()
    if db_project.status in {ProjectStatus.STREAMING, ProjectStatus.SIMULATING} and not enabled:
        timeout = 15
        while not enabled and timeout > 0:
            await asyncio.sleep(1)
            streaming_project = memory.streaming_projects.get(project_id)
            enabled = streaming_project and not streaming_project["finished"].is_set()
            timeout -= 1
    if not enabled:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_STREAMING)

    # Check if the project is already being read
    if streaming_project["reading"]:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_ALREADY_READING)
    else:
        streaming_project["reading"] = True

    return EventSourceResponse(
        content=event_generator(request, db, project_id),
        headers={"Content-Type": "text/event-stream"},
        ping=15
    )


@router.get("/{project_id}/dataset/{dataset_type}")
def download_project_dataset(request: Request, project_id: int, dataset_type: str,
                             background_tasks: BackgroundTasks, db: Session = Depends(get_db),
                             _: bool = Depends(validate_token)):
    logger.warning(f"Download dataset <{dataset_type}> of project {project_id} - from IP {get_real_ip(request)}")

    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)
    elif (dataset_type in {"processed", "ongoing", "simulation"}
          and db_project.status not in ProjectStatusGroup.PROCESSED):
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_PREPROCESSED)

    if dataset_type == "original":
        temp_path = get_original_dataset_path(db_project.event_log)
    elif dataset_type == "processed":
        temp_path = get_processed_dataset_path(db_project.event_log)
    elif dataset_type == "ongoing":
        temp_path = get_ongoing_dataset_path(db_project.event_log)
    elif dataset_type == "simulation":
        temp_path = get_simulation_dataset_path(db_project.event_log)
    else:
        raise HTTPException(status_code=400, detail=ErrorType.INVALID_DATASET_TYPE)

    if not temp_path:
        raise HTTPException(status_code=400, detail=ErrorType.PROCESS_DATASET_ERROR)

    background_tasks.add_task(delete_file, temp_path)
    return FileResponse(temp_path, filename=temp_path.split("/")[-1])
