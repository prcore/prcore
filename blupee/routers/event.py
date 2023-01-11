import logging

from fastapi import APIRouter
from pydantic import BaseModel

from blupee import glovar
from blupee.models.case import Case
from blupee.models.event import Event
from blupee.models.identifier import get_identifier

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event")


class Request(BaseModel):
    case_id: int
    dashboard_id: int
    activity: str
    start_timestamp: int
    end_timestamp: int
    resource: str = ""
    attributes: dict = {}
    status: str


@router.post("")
def receive_event(request: Request):
    # Create new event
    dash_board_id = request.dashboard_id

    # Find dashboard
    with glovar.save_lock:
        for dashboard in glovar.dashboards:
            if dashboard.id == dash_board_id:
                break
        else:
            return {"message": "Dashboard not found"}

    print("Event received")

    # Create new event
    event = Event(
        id=get_identifier(),
        activity=request.activity,
        start_timestamp=request.start_timestamp,
        end_timestamp=request.end_timestamp,
        resource=request.resource,
        attributes=request.attributes
    )
    event.save(new=True)
    print("Event created")

    # Find case
    case_id = request.case_id

    for case in dashboard.current_event_log.cases:
        if case.id == case_id:
            break
    else:
        # Create new case
        case = Case(
            id=case_id,
            status="ongoing",
            events=[],
            results=[]
        )
        case.save(new=True)
        dashboard.current_event_log.cases.append(case)
        print("Case created")

    # Append event to case
    case.status = request.status
    case.events.append(event)
    print("Event appended to case")
    case.prescribe(dashboard.algorithms)
    print(f"Result: {case.get_predicted_result()}")
    case.save()

    return {"message": "Event received", "case": case}