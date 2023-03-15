import logging
from copy import deepcopy
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as event_log_crud
import core.crud.project as project_crud
import core.schemas.request.event_log as event_log_request
import core.schemas.response.event_log as event_log_response
import core.schemas.event_log as event_log_schema
from core.confs import path
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus
from core.functions.common.etc import get_current_time_label
from core.functions.common.request import get_real_ip, get_db
from core.functions.common.file import get_extension, get_new_path
from core.functions.definition.util import get_available_options
from core.functions.event_log.analysis import get_activities_count, get_brief_with_inferred_definition
from core.functions.event_log.dataset import get_completed_transition_df
from core.functions.event_log.df import get_dataframe, save_dataframe
from core.functions.event_log.job import set_definition
from core.functions.event_log.file import get_dataframe_from_file
from core.security.token import validate_token
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


@router.post("", response_model=event_log_response.UploadEventLogResponse)
def upload_event_log(request: Request, file: UploadFile = Form(), separator: str = Form(","),
                     test: UploadFile = Form(None),
                     db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Upload event log <{file and file.filename}> - from IP {get_real_ip(request)}")

    if not file or not file.file or (extension := get_extension(file.filename)) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    if test and test.file and get_extension(test.filename) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    # Save the file
    raw_path = get_new_path(
        base_path=f"{path.EVENT_LOG_RAW_PATH}/",
        prefix=f"{get_current_time_label()}-",
        suffix=f".{extension}"
    )

    with open(raw_path, "wb") as f:
        f.write(file.file.read())

    # Get dataframe from file
    df = get_dataframe_from_file(raw_path, extension, separator)

    db_event_log = event_log_crud.create_event_log(db, event_log_schema.EventLogCreate(
        file_name=file.filename,
        saved_name=raw_path.split("/")[-1]
    ))
    save_dataframe(db, db_event_log, df)
    brief = get_brief_with_inferred_definition(df)

    # Save test file to memory
    if test and test.file:
        memory.log_tests[db_event_log.id] = {
            "date": datetime.now(),
            "file": deepcopy(test.file),
            "extension": get_extension(test.filename),
            "separator": separator
        }

    return {
        "message": "Event log uploaded",
        "event_log_id": db_event_log.id,
        "columns_header": brief[0],
        "columns_inferred_definition": brief[1],
        "columns_data": brief[2:]
    }


@router.put("/{event_log_id}", response_model=event_log_response.UpdateEventLogResponse)
def update_event_log(request: Request, event_log_id: int, update_body: event_log_request.ColumnsDefinitionRequest,
                     db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update event log {event_log_id} - from IP {get_real_ip(request)}")
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_NOT_FOUND)
    db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)

    if db_project and db_project.status not in {ProjectStatus.WAITING, ProjectStatus.TRAINED, ProjectStatus.STREAMING,
                                                ProjectStatus.SIMULATING, ProjectStatus.ERROR}:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_READY)

    df = get_dataframe(db_event_log)

    if not update_body.fast_mode and df.shape[0] > 500000:
        raise HTTPException(status_code=400, detail=ErrorType.FAST_MODE_ENFORCED)

    db_event_log = set_definition(db, db_event_log, update_body)
    df = get_completed_transition_df(df, update_body.columns_definition)

    return {
        "message": "Event log updated",
        "event_log_id": db_event_log.id,
        "received_definition": db_event_log.definition.columns_definition,
        "activities_count": get_activities_count(df, db_event_log.definition.columns_definition),
        "outcome_options": get_available_options(db_event_log.definition.columns_definition, "outcome"),
        "treatment_options": get_available_options(db_event_log.definition.columns_definition, "treatment")
    }


@router.get("/all", response_model=event_log_response.AllEventLogsResponse)
def read_event_logs(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                    _: bool = Depends(validate_token)):
    logger.warning(f"Read event logs - from IP {get_real_ip(request)}")
    return {
        "message": "Event logs retrieved successfully",
        "event_logs": event_log_crud.get_event_logs(db, skip, limit)
    }


@router.get("/{event_log_id}/definition", response_model=event_log_response.EventLogDefinitionResponse)
def read_event_log_definition(request: Request, event_log_id: int, db: Session = Depends(get_db),
                              _: bool = Depends(validate_token)):
    logger.warning(f"Read event log definition for {event_log_id} - from IP {get_real_ip(request)}")
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_NOT_FOUND)

    if not db_event_log.definition:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_DEFINITION_NOT_FOUND)

    df = get_dataframe(db_event_log)
    brief = get_brief_with_inferred_definition(df)

    return {
        "message": "Event log definition retrieved successfully",
        "event_log_id": db_event_log.id,
        "columns_header": list(db_event_log.definition.columns_definition.keys()),
        "columns_old_definition": list(db_event_log.definition.columns_definition.values()),
        "columns_data": brief[2:]
    }


@router.get("/{event_log_id}", response_model=event_log_response.EventLogResponse)
def read_event_log(request: Request, event_log_id: int, db: Session = Depends(get_db),
                   _: bool = Depends(validate_token)):
    logger.warning(f"Read event log {event_log_id} - from IP {get_real_ip(request)}")
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_NOT_FOUND)

    return {
        "message": "Event log retrieved successfully",
        "event_log": db_event_log
    }
