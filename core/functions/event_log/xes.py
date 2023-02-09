import logging
from typing import Union

from fastapi import UploadFile
from pandas import DataFrame
from pm4py import read_xes, write_xes

from core.confs import path
from core.models import PreviousEventLog
from core.models.case import Case
from core.models.event import Event
from core.models.identifier import get_identifier
from core.functions.general.file import get_new_path

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_xes(path: str) -> DataFrame:
    # Get dataframe from xes file
    return read_xes(path)

def process_xes_file(path: str, file: UploadFile) -> Union[PreviousEventLog, None]:
    # Process xes file
    result = None

    try:
        # Try to read the file, then save it as new file
        event_log = read_xes(path)

        if not event_log:
            return None

        new_path = get_new_path(
            base_path=f"{path.EVENT_LOG_PREVIOUS_PATH}/",
            suffix=".xes"
        )
        write_xes(event_log, new_path)

        cases = []

        for i in range(len(event_log)):
            new_case = Case(
                id=get_identifier(),
                name=f"Case {i}",
                status="closed",
                events=[],
                results=[]
            )
            new_case.save()
            for j in event_log[i]:
                should_pass = False
                event_dict = {
                    "id": get_identifier(),
                    "activity": "",
                    "timestamp": "",
                    "resource": "",
                    "attributes": {}
                }
                for key in j:
                    if key == "lifecycle:transition" and j[key] != "complete":
                        should_pass = True
                        continue
                    if "activity" in key.lower() or "concept:name" in key.lower():
                        event_dict["activity"] = j[key]
                    elif "timestamp" in key.lower():
                        event_dict["timestamp"] = str(j[key])
                    elif "resource" in key.lower():
                        event_dict["resource"] = j[key]
                    else:
                        event_dict["attributes"][key] = j[key]
                if should_pass:
                    continue
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

        # Create the previous event log
        result = PreviousEventLog(
            id=get_identifier(),
            name=file.filename,
            path=new_path,
            cases=cases
        )
    except Exception as e:
        logger.warning(f"Process xes file error: {e}", exc_info=True)

    return result
