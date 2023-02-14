import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as event_log_crud
import core.crud.definition as definition_crud
import core.schemas.response.event_log as event_log_response
import core.schemas.event_log as event_log_schema
import core.schemas.definition as definition_schema
from core.confs import path
from core.functions.definition.util import get_available_options
from core.functions.event_log.analysis import get_activities_count, get_brief_with_inferred_definition
from core.functions.event_log.csv import get_dataframe_from_csv
from core.functions.event_log.dataset import get_completed_transition_df
from core.functions.event_log.df import get_dataframe, save_dataframe
from core.functions.event_log.xes import get_dataframe_from_xes
from core.functions.event_log.validation import validate_column_definition
from core.functions.event_log.zip import get_dataframe_from_zip
from core.functions.general.etc import get_current_time_label
from core.functions.general.request import get_real_ip, get_db
from core.functions.general.file import get_extension, get_new_path
from core.security.token import validate_token

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


@router.post("", response_model=event_log_response.UploadEventLogResponse)
def upload_event_log(request: Request, file: UploadFile = Form(), seperator: str = Form(","),
                     db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Upload event log: {file} - from IP {get_real_ip(request)}")

    if not file or not file.file or (extension := get_extension(file.filename)) not in path.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="No valid file provided")

    # Save the file
    raw_path = get_new_path(
        base_path=f"{path.EVENT_LOG_RAW_PATH}/",
        prefix=f"{get_current_time_label()}-",
        suffix=f".{extension}"
    )

    with open(raw_path, "wb") as f:
        f.write(file.file.read())

    # Get dataframe from file
    if extension == "xes":
        df = get_dataframe_from_xes(raw_path)
    elif extension == "csv":
        df = get_dataframe_from_csv(raw_path, seperator)
    else:
        df = get_dataframe_from_zip(raw_path, seperator)

    db_event_log = event_log_crud.create_event_log(db, event_log_schema.EventLogCreate(
        file_name=file.filename,
        saved_name=raw_path.split("/")[-1]
    ))
    save_dataframe(db, db_event_log, df)
    brief = get_brief_with_inferred_definition(df)

    return {
        "message": "Event log uploaded",
        "event_log_id": db_event_log.id,
        "columns_header": brief[0],
        "columns_inferred_definition": brief[1],
        "columns_data": brief[2:]
    }


@router.put("/{event_log_id}", response_model=event_log_response.UpdateEventLogResponse)
async def update_event_log(request: Request, event_log_id: int,
                           db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update event log: {event_log_id} - from IP {get_real_ip(request)}")
    request_body = await request.json()
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail="Event log not found")

    df = get_dataframe(db_event_log)
    validate_column_definition(request_body, df)
    df = get_completed_transition_df(df, request_body)

    if db_event_log.definition:
        db_definition = definition_crud.update_definition(db, definition_schema.Definition(
            id=db_event_log.definition.id,
            columns_definition=request_body,
            outcome_definition=db_event_log.definition.outcome_definition,
            treatment_definition=db_event_log.definition.treatment_definition
        ))
    else:
        db_definition = definition_crud.create_definition(db, definition_schema.DefinitionCreate(
            columns_definition=request_body
        ))

    db_event_log = event_log_crud.associate_definition(db, event_log_id, db_definition.id)

    return {
        "message": "Event log updated",
        "event_log_id": db_event_log.id,
        "received_definition": db_definition.columns_definition,
        "activities_count": get_activities_count(df, db_definition.columns_definition),
        "outcome_options": get_available_options(db_definition.columns_definition, "outcome"),
        "treatment_options": get_available_options(db_definition.columns_definition, "treatment")
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
    logger.warning(f"Read event log definition: {event_log_id} - from IP {get_real_ip(request)}")
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail="Event log not found")

    if not db_event_log.definition:
        raise HTTPException(status_code=404, detail="Event log definition not found")

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
    logger.warning(f"Read event log: {event_log_id} - from IP {get_real_ip(request)}")
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail="Event log not found")

    return {
        "message": "Event log retrieved successfully",
        "event_log": db_event_log
    }
