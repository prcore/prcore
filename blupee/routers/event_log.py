import logging
from typing import Union

from fastapi import APIRouter, UploadFile
from pm4py import read_xes, write_xes

from blupee import confs
from blupee.utils.file import get_extension, get_new_path

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


@router.post("")
def upload_event_log(file: Union[UploadFile, None] = None):
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

    # Try to read the file, then save it as new file
    event_log = read_xes(tmp_path)

    if not event_log:
        return {"message": "File not valid"}

    new_path = get_new_path(
        base_path=f"{confs.EVENT_LOG_PREVIOUS_PATH}/",
        suffix=f".{original_extension}"
    )
    write_xes(event_log, new_path)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "new_path": new_path
    }
