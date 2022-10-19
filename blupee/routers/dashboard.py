import logging

from fastapi import APIRouter
from pydantic import BaseModel

from blupee import confs, glovar
from blupee.models import PreviousEventLog, CurrentEventLog
from blupee.models.dashboard import Dashboard
from blupee.models.identifier import get_identifier
from blupee.utils.file import get_new_path

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/dashboard")


class Request(BaseModel):
    event_log_id: int
    algorithms: dict


@router.post("")
def new_dashboard(request: Request):
    # Get previous event log by reqeust.event_log_id
    with glovar.save_lock:
        for previous_event_log in glovar.previous_event_logs:
            if previous_event_log.id == request.event_log_id:
                break
        else:
            return {"message": "Event log not found"}

    # Get algorithms by request.algorithms
    algorithms = []
    previous_event_log: PreviousEventLog
    algo_objs = [Algo(previous_event_log.path) for Algo in glovar.algo_classes]

    for algorithm_name in request.algorithms:
        for algorithm in algo_objs:
            if algorithm.name == algorithm_name:
                algorithm.parameters = request.algorithms[algorithm_name]
                algorithms.append(algorithm)
                break
        else:
            return {"message": "Algorithm not found"}

    # Create new current event log
    current_event_log = CurrentEventLog(
        id=get_identifier(),
        name=previous_event_log.name,
        path=get_new_path(confs.EVENT_LOG_CURRENT_PATH + "/", suffix=".xes"),
        cases=[]
    )
    current_event_log.save()

    # Create new dashboard
    new_dashboard_obj = Dashboard(
        id=get_identifier(),
        name=previous_event_log.name,
        description="New dashboard",
        previous_event_log=previous_event_log,
        current_event_log=current_event_log,
        algorithms=algorithms,
        training_tasks=[],
        prescribing_tasks=[],
    )
    new_dashboard_obj.save()

    return {"message": "Dashboard created", "dashboard": new_dashboard_obj}
