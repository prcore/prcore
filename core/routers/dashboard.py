import logging
from threading import Thread
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from core import confs, glovar
from core.models import PreviousEventLog, CurrentEventLog
from core.models.dashboard import Dashboard
from core.models.identifier import get_identifier
from core.models.training_task import TrainingTask, TrainingTaskResponse
from core.models.prescribing_task import PrescribingTask
from core.functions.general import get_new_path

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/dashboard")


class Request(BaseModel):
    event_log_id: int
    algorithms: dict


class AlgorithmOutput(BaseModel):
    name: str
    description: str
    training_task: TrainingTaskResponse


class DashboardResponse(BaseModel):
    id: int
    name: str
    description: str = ""
    training_tasks: List[TrainingTaskResponse]
    prescribing_tasks: List[PrescribingTask]


class Response(BaseModel):
    message: str
    dashboard: DashboardResponse = None


class DashboardListResponse(BaseModel):
    message: str
    dashboards: List[DashboardResponse] = []


@router.post("", response_model=Response)
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
    algo_objs = [Algo(previous_event_log.cases) for Algo in glovar.algo_classes]

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

    # Create new training task
    trainings = []
    for algorithm in algorithms:
        training_task = TrainingTask(
            id=get_identifier(),
            status="training",
        )
        training_task.save()
        trainings.append(training_task)
        algorithm.training_task = training_task
        t = Thread(target=algorithm.train)
        t.daemon = True
        t.start()

    # Create new dashboard
    new_dashboard_obj = Dashboard(
        id=get_identifier(),
        name=previous_event_log.name,
        description="New dashboard",
        previous_event_log=previous_event_log,
        current_event_log=current_event_log,
        algorithms=algorithms,
        training_tasks=trainings,
        prescribing_tasks=[],
    )
    new_dashboard_obj.save()

    return {"message": "Dashboard created", "dashboard": new_dashboard_obj}


@router.get("/{dashboard_id}", response_model=Response)
def get_dashboard_by_id(dashboard_id: int):
    for dashboard in glovar.dashboards:
        if dashboard.id == dashboard_id:
            return {"message": "Dashboard found", "dashboard": dashboard}

    return {"message": "Dashboard not found"}


@router.get("", response_model=DashboardListResponse)
def get_all_dashboards():
    return {"message": "Dashboards found", "dashboards": glovar.dashboards}
