import logging
from typing import Union

from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy.orm import Session

import core.crud.event_log as crud
import core.models.event_log as model
import core.responses.event_log as response
import core.schemas.event_log as schema
from core import confs, glovar
from core.functions.event_log.csv import process_csv_file
from core.functions.event_log.xes import process_xes_file
from core.security.token import validate_token
from core.functions.general.file import get_extension, get_new_path

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


def get_db(request: Request):
    return request.state.db


@router.post("")
def upload_event_log(file: Union[UploadFile, None] = None, _: bool = Depends(validate_token)):
    logger.warning(f"Upload event log: {file}")

    if not file or not file.file:
        return {"message": "No valid file provided"}

    # Save the file
    original_extension = get_extension(file.filename)

    if original_extension not in confs.ALLOWED_EXTENSIONS:
        return {"message": "File extension not allowed"}

    tmp_path = get_new_path(
        base_path=f"{confs.TEMP_PATH}/",
        prefix="event_log_",
        suffix=f".{original_extension}"
    )

    with open(tmp_path, "wb") as f:
        f.write(file.file.read())

    if original_extension == "xes":
        previous_event_log = process_xes_file(tmp_path, file)
    elif original_extension == "csv":
        previous_event_log = process_csv_file(tmp_path, file.filename)
    else:
        previous_event_log = None

    if previous_event_log is None:
        return {"message": "File not valid"}
    else:
        previous_event_log.save()

    return {
        "message": "File uploaded successfully",
        "previous_event_log": {
            "id": previous_event_log.id,
            "name": previous_event_log.name,
            "path": previous_event_log.path,
            "cases": previous_event_log.cases[:10]
        }
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
    return crud.get_event_logs(db, skip=skip, limit=limit)
