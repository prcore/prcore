import asyncio
import logging

from fastapi import BackgroundTasks, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
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
import core.models.event_log as event_log_model
import core.models.project as project_model
import core.schemas.request.project as project_request
import core.schemas.definition as definition_schema
import core.schemas.project as project_schema
from core.confs import path
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus, ProjectStatusGroup, PluginStatus
from core.functions.common.file import delete_file, get_extension
from core.functions.plugin.util import enhance_additional_infos, get_active_plugins
from core.functions.event_log.dataset import (get_ongoing_dataset_path, get_original_dataset_path,
                                              get_processed_dataset_path, get_simulation_dataset_path)
from core.functions.event_log.job import start_pre_processing
from core.functions.message.sender import send_streaming_prepare_to_all_plugins
from core.functions.project.prescribe import (delete_result_from_memory, get_ongoing_dataset_result_key,
                                              process_ongoing_dataset, run_project_watcher_for_ongoing_dataset)
from core.functions.project.streaming import event_generator, disable_streaming
from core.functions.project.validation import (validate_project_definition, validate_project_status,
                                               validate_streaming_status)
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def process_project_creation(create_body: project_request.CreateProjectRequest, db: Session) -> dict:
    # Get the data from the database, and validate it
    db_event_log = event_log_crud.get_event_log(db, create_body.event_log_id)
    if not db_event_log:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_NOT_FOUND)
    elif not db_event_log.definition or not db_event_log.definition.columns_definition:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_DEFINITION_NOT_FOUND)
    db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)
    if db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_EXISTED)

    # Validate and get the user's input
    outcome_definition, outcome_negative, treatment = get_definitions_from_request(create_body, db_event_log)

    # Create the project
    definition_crud.set_project_level_definition(
        db=db,
        db_definition=db_event_log.definition,
        outcome=outcome_definition,
        outcome_negative=outcome_negative,
        treatment=treatment
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
    start_pre_processing(db_project.id, get_active_plugins(), create_body.parameters, create_body.additional_info)

    # Start the test file watching
    result_key and run_project_watcher_for_ongoing_dataset(db_project.id, result_key)

    return {
        "message": "Project created successfully",
        "project": db_project,
        "result_key": result_key
    }


def get_definitions_from_request(
        request_body: project_request.CreateProjectRequest | project_request.UpdateProjectRequest,
        db_event_log: event_log_model.EventLog
) -> tuple[list[list[definition_schema.ProjectDefinition]] | None,
           bool,
           list[definition_schema.ProjectDefinition] | None]:
    columns_definition = db_event_log.definition.columns_definition
    positive_outcome = request_body.positive_outcome
    negative_outcome = request_body.negative_outcome
    outcome_definition: list[list[definition_schema.ProjectDefinition]] | None = None
    outcome_negative = False
    treatment = request_body.treatment
    if positive_outcome and negative_outcome:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_DEFINITION_CONFLICT)
    elif positive_outcome:
        validate_project_definition(positive_outcome, columns_definition)
        outcome_definition = positive_outcome
    elif negative_outcome:
        validate_project_definition(negative_outcome, columns_definition)
        outcome_definition = negative_outcome
        outcome_negative = True
    treatment and validate_project_definition(treatment, columns_definition)
    return outcome_definition, outcome_negative, treatment


def process_projects_reading(db: Session):
    return paginate(db, select(project_model.Project).order_by(desc(project_model.Project.created_at)))  # type: ignore


def process_project_reading(project_id: int, db: Session):
    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)

    return {
        "message": "Project retrieved successfully",
        "project": db_project
    }


def process_project_update(project_id: int, update_body: project_request.BasicUpdateProjectRequest,
                           db: Session) -> dict:
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


def process_project_definition_update(project_id: int, update_body: project_request.UpdateProjectRequest,
                                      db: Session) -> dict:
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

    # Validate and get the user's input
    outcome_definition, outcome_negative, treatment = get_definitions_from_request(update_body, db_event_log)
    disable_streaming(db, db_project, True)

    # Update the project
    definition_crud.set_project_level_definition(
        db=db,
        db_definition=db_event_log.definition,
        outcome=outcome_definition,
        outcome_negative=outcome_negative,
        treatment=treatment
    )

    # Start the pre-processing
    project_crud.update_status(db, db_project, ProjectStatus.PREPROCESSING)
    start_pre_processing(db_project.id, get_active_plugins(), update_body.parameters, update_body.additional_info,
                         redefined=True)

    return {
        "message": "Project definition updated successfully",
        "project": db_project
    }


def process_project_deletion(project_id: int, db: Session) -> dict:
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


def process_ongoing_dataset_uploading(project_id: int, background_tasks: BackgroundTasks, file: UploadFile,
                                      seperator: str, db: Session) -> dict:
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


def process_ongoing_dataset_result(project_id: int, result_key: str, background_tasks: BackgroundTasks,
                                   db: Session) -> dict:
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
            if case_id not in result["cases"]:
                continue
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


def process_stream_starting(project_id: int, streaming_type: str, db: Session) -> dict:
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


def process_stream_stopping(project_id: int, db: Session) -> dict:
    # Get the data from the database, and validate it
    db_project = project_crud.get_project_by_id(db, project_id)
    validate_streaming_status(db_project, "stop")

    # Stop the streaming
    disable_streaming(db, db_project)

    return {
        "message": "Project streaming stopped successfully",
        "project_id": project_id
    }


def process_stream_clearing(project_id: int, db: Session) -> dict:
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


async def process_stream_result(request: Request, project_id: int, db: Session) -> EventSourceResponse:
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


def process_dataset_downloading(project_id: int, dataset_type: str, background_tasks: BackgroundTasks,
                                db: Session) -> FileResponse:
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
