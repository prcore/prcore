import logging
from copy import deepcopy
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as event_log_crud
import core.crud.project as project_crud
import core.schemas.definition as definition_schema
import core.schemas.request.event_log as event_log_request
import core.schemas.event_log as event_log_schema
from core.confs import path
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus
from core.functions.common.file import get_extension
from core.functions.definition.util import get_available_options
from core.functions.event_log.analysis import get_activities_count, get_brief_with_inferred_definition
from core.functions.event_log.dataset import get_completed_transition_df
from core.functions.event_log.df import get_dataframe, get_df_from_uploaded_file, save_dataframe
from core.functions.event_log.job import set_definition, start_pre_processing
from core.functions.plugin.util import get_active_plugins, enhance_additional_infos
from core.functions.project.streaming import disable_streaming
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def process_uploaded_event_log(file: UploadFile, separator: str, test: UploadFile, db: Session) -> dict:
    if not file or not file.file or (extension := get_extension(file.filename)) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    if test and test.file and get_extension(test.filename) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    # Get the dataframe from the uploaded file
    df, raw_path = get_df_from_uploaded_file(file, extension, separator)

    # Save the event log to the database
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


def process_event_log_definition(event_log_id: int, update_body: event_log_request.ColumnsDefinitionRequest,
                                 db: Session) -> dict:
    db_event_log = event_log_crud.get_event_log(db, event_log_id)
    if not db_event_log:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_NOT_FOUND)

    db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)
    if db_project and db_project.status not in {ProjectStatus.WAITING, ProjectStatus.TRAINED, ProjectStatus.STREAMING,
                                                ProjectStatus.SIMULATING, ProjectStatus.ERROR}:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_READY)

    df = get_dataframe(db_event_log)

    if not update_body.fast_mode and df.shape[0] > 1000000:
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


def process_re_uploaded_event_log(event_log_id: int, file: UploadFile, separator: str, db: Session) -> dict:
    if not file or not file.file or (extension := get_extension(file.filename)) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_INVALID)

    db_event_log = event_log_crud.get_event_log(db, event_log_id)
    if not db_event_log:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_NOT_FOUND)

    db_project = project_crud.get_project_by_event_log_id(db, db_event_log.id)
    if not db_project:
        raise HTTPException(status_code=404, detail=ErrorType.PROJECT_NOT_FOUND)
    elif db_project.status not in {ProjectStatus.TRAINED, ProjectStatus.STREAMING, ProjectStatus.SIMULATING,
                                   ProjectStatus.ERROR}:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_READY)

    # Get the dataframe from the uploaded file
    df, raw_path = get_df_from_uploaded_file(file, extension, separator)

    # Check if the columns match the definition
    defined_columns = db_event_log.definition.columns_definition
    df_columns = df.columns.tolist()
    if not all([col in df_columns for col in defined_columns]):
        raise HTTPException(status_code=400, detail=ErrorType.EVENT_LOG_COLUMNS_MISMATCH)
    if not db_event_log.definition.fast_mode and df.shape[0] > 1000000:
        raise HTTPException(status_code=400, detail=ErrorType.FAST_MODE_ENFORCED)

    # Disable streaming
    disable_streaming(db, db_project, redefined=True)

    # Update the event log in the database
    db_event_log = event_log_crud.update_event_log(db, db_event_log, file.filename, raw_path.split("/")[-1])

    # Start processing the event log
    active_plugins = get_active_plugins()
    parameters = {db_plugin.key: db_plugin.parameters for db_plugin in db_project.plugins}
    additional_infos = {db_plugin.key: db_plugin.additional_info for db_plugin in db_project.plugins}
    enhanced_additional_infos = enhance_additional_infos(
        additional_infos=additional_infos,
        active_plugins=active_plugins,
        definition=definition_schema.Definition.from_orm(db_event_log.definition)
    )
    start_pre_processing(db_project.id, active_plugins, parameters, enhanced_additional_infos, redefined=True)

    # Get the completed transition dataframe
    df = get_completed_transition_df(df, db_event_log.definition.columns_definition)

    return {
        "message": "Event log updated",
        "event_log_id": db_event_log.id,
        "received_definition": db_event_log.definition.columns_definition,
        "activities_count": get_activities_count(df, db_event_log.definition.columns_definition),
        "outcome_options": get_available_options(db_event_log.definition.columns_definition, "outcome"),
        "treatment_options": get_available_options(db_event_log.definition.columns_definition, "treatment")
    }


def process_event_logs_reading(skip: int, limit: int, db: Session) -> dict:
    return {
        "message": "Event logs retrieved successfully",
        "event_logs": event_log_crud.get_event_logs(db, skip, limit)
    }


def process_event_log_definition_reading(event_log_id: int, db: Session):
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


def process_event_log_reading(event_log_id: int, db: Session) -> dict:
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail=ErrorType.EVENT_LOG_NOT_FOUND)

    return {
        "message": "Event log retrieved successfully",
        "event_log": db_event_log
    }
