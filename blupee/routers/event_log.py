import logging
from typing import Union

from fastapi import APIRouter, UploadFile
from pm4py import read_xes, write_xes

from blupee import confs, glovar
from blupee.models import PreviousEventLog
from blupee.models.case import Case
from blupee.models.event import Event
from blupee.models.identifier import get_identifier
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

    cases = []

    for i in range(len(event_log)):
        new_case = Case(
            id=get_identifier(),
            name=f"Case {i}",
            status="closed",
            events=[]
        )
        new_case.save()
        for j in event_log[i]:
            event_dict = {
                "id": get_identifier(),
                "activity": "",
                "timestamp": "",
                "resource": "",
                "attributes": {}
            }
            for key in j:
                if "activity" in key.lower():
                    event_dict["activity"] = j[key]
                elif "timestamp" in key.lower():
                    event_dict["timestamp"] = str(j[key])
                elif "resource" in key.lower():
                    event_dict["resource"] = j[key]
                else:
                    event_dict["attributes"][key] = j[key]
            new_event = Event(
                id=event_dict["id"],
                activity=event_dict["activity"],
                timestamp=event_dict["timestamp"],
                resource=event_dict["resource"],
                attributes=event_dict["attributes"],
            )
            new_event.save()
            new_case.events.append(new_event)
        new_case.save()
        cases.append(new_case)

    # Save the event log to the database
    previous_event_log = PreviousEventLog(
        id=get_identifier(),
        name=file.filename,
        path=new_path,
        cases=cases
    )
    previous_event_log.save()

    return {
        "message": "File uploaded successfully",
        "previous_event_log": previous_event_log
    }


@router.put("/{event_id}")
def confirm_event_log(event_id: int):
    with glovar.save_lock:
        for i in range(len(glovar.previous_event_logs)):
            if glovar.previous_event_logs[i].id == event_id:
                previous_event_log = glovar.previous_event_logs[i]

    algo_objects = []

    for Algorithm in glovar.algo_classes:
        algorithm = Algorithm(data_path=previous_event_log.path)
        algorithm.is_applicable() and algo_objects.append(algorithm)

    algo_dict = {}

    for algorithm in algo_objects:
        algo_dict[algorithm.name] = {
            "description": algorithm.description,
            "parameters": algorithm.parameters
        }

    return {
        "message": "Event log confirmed, please select algorithm and set parameters",
        "applicable_algorithms": algo_dict
    }
