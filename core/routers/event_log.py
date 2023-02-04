import logging
from typing import Union

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as crud
import core.models.event_log as model
import core.responses.event_log as response
import core.schemas.event_log as schema
from core import confs, glovar
from core.functions.event_log.analysis import get_brief_with_inferred_definition
from core.functions.event_log.csv import get_dataframe_from_csv
from core.functions.event_log.xes import get_dataframe_from_xes
from core.security.token import validate_token
from core.functions.general.file import get_extension, get_new_path

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


def get_db(request: Request):
    return request.state.db


@router.post("", response_model=response.UploadEventLogResponse)
def upload_event_log(file: UploadFile = Form(), seperator: str = Form(","), _: bool = Depends(validate_token)):
    logger.warning(f"Upload event log: {file}")

    if not file or not file.file or (extension := get_extension(file.filename)) not in confs.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="No valid file provided")

    # Save the file
    raw_path = get_new_path(
        base_path=f"{confs.RAW_EVENT_LOG_PATH}/",
        prefix="event_log_",
        suffix=f".{extension}"
    )

    with open(raw_path, "wb") as f:
        f.write(file.file.read())

    # Get dataframe from file
    df = get_dataframe_from_xes(raw_path) if extension == "xes" else get_dataframe_from_csv(raw_path, seperator)
    brief = get_brief_with_inferred_definition(df)

    return {
        "message": "Event log uploaded",
        "event_log_id": 1,
        "columns_header": brief[0],
        "columns_inferred_definition": brief[1],
        "columns_data": brief[2:]
    }

@router.get("/all", response_model=response.AllEventLogsResponse)
def read_all_event_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    return {
        "message": "All event logs retrieved successfully",
        "event_logs": crud.get_event_logs(db, skip, limit)
    }
