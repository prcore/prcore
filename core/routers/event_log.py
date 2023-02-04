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
def upload_event_log(file: UploadFile = Form(), _: bool = Depends(validate_token)):
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

    df = get_dataframe_from_xes(raw_path)
    return {
        "message": "Event log uploaded",
        "event_log_id": 1,
        "events_brief": get_brief_with_inferred_definition(df)
    }


# @router.put("/{event_id}")
# def confirm_event_log(event_id: int, _: bool = Depends(validate_token)):
#     with glovar.save_lock:
#         for i in range(len(glovar.previous_event_logs)):
#             if glovar.previous_event_logs[i].id == event_id:
#                 previous_event_log = glovar.previous_event_logs[i]
#
#     algo_objects = []
#
#     for Algorithm in glovar.algo_classes:
#         algorithm = Algorithm(data=previous_event_log.cases)
#         algorithm.is_applicable() and algo_objects.append(algorithm)
#
#     algo_dict = {}
#
#     for algorithm in algo_objects:
#         algo_dict[algorithm.name] = {
#             "description": algorithm.description,
#             "parameters": algorithm.parameters
#         }
#
#     return {
#         "message": "Event log confirmed, please select algorithm and set parameters",
#         "applicable_algorithms": algo_dict
#     }


@router.get("/all", response_model=response.AllEventLogsResponse)
def read_all_event_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    return {
        "message": "All event logs retrieved successfully",
        "event_logs": crud.get_event_logs(db, skip, limit)
    }
