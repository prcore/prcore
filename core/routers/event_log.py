import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as event_log_crud
import core.crud.definition as definition_crud
import core.responses.event_log as event_log_response
import core.schemas.event_log as event_log_schema
import core.schemas.definition as definition_schema
from core import confs
from core.functions.event_log.analysis import get_brief_with_inferred_definition
from core.functions.event_log.csv import get_dataframe_from_csv
from core.functions.event_log.xes import get_dataframe_from_xes
from core.functions.general.etc import get_current_time_label
from core.security.token import validate_token
from core.functions.general.file import get_extension, get_new_path

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


def get_db(request: Request):
    return request.state.db


@router.post("", response_model=event_log_response.UploadEventLogResponse)
def upload_event_log(request: Request, file: UploadFile = Form(), seperator: str = Form(","),
                     db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Upload event log: {file} - from IP {request.client.host}")

    if not file or not file.file or (extension := get_extension(file.filename)) not in confs.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="No valid file provided")

    # Save the file
    raw_path = get_new_path(
        base_path=f"{confs.RAW_EVENT_LOG_PATH}/",
        prefix=f"{get_current_time_label()}-",
        suffix=f".{extension}"
    )

    with open(raw_path, "wb") as f:
        f.write(file.file.read())

    # Get dataframe from file
    df = get_dataframe_from_xes(raw_path) if extension == "xes" else get_dataframe_from_csv(raw_path, seperator)
    db_event_log = event_log_crud.create_event_log(db, event_log_schema.EventLogCreate(
        file_name=file.filename,
        saved_name=raw_path.split("/")[-1]
    ))
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
    logger.warning(f"Update event log: {event_log_id} - from IP {request.client.host}")
    request_body = await request.json()
    db_event_log = event_log_crud.get_event_log(db, event_log_id)

    if not db_event_log:
        raise HTTPException(status_code=404, detail="Event log not found")

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

    db_event_log = event_log_crud.update_event_log(db, event_log_id, db_definition.id)

    return {
        "message": "Event log updated",
        "event_log_id": db_event_log.id,
        "activities_count": {
            "A": 53,
            "B": 20,
            "C": 12
        },
        "outcome_selections": [
            "TEXT",
            "NUMBER",
            "BOOLEAN",
            "TIMESTAMP",
            "ACTIVITY",
            "DURATION",
            "COST"
        ],
        "treatment_selections": [
            "ACTIVITY",
            "RESOURCE",
            "DURATION"
        ]
    }


@router.get("/all", response_model=event_log_response.AllEventLogsResponse)
def read_all_event_logs(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                        _: bool = Depends(validate_token)):
    logger.warning(f"Read all event logs - from IP {request.client.host}")
    result = {
        "message": "All event logs retrieved successfully",
        "event_logs": event_log_crud.get_event_logs(db, skip, limit)
    }
    return result
