import logging
from typing import List

from fastapi import APIRouter

from blupee import glovar
from blupee.models import CurrentEventLog
from blupee.models.case import Case

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/result")


@router.get("/{dashboard_id}")
def get_results_by_dashboard_id(dashboard_id: int):
    for dashboard in glovar.dashboards:
        if dashboard.id == dashboard_id:
            break
    else:
        return {"message": "Dashboard not found"}

    current_event_log: CurrentEventLog = dashboard.current_event_log
    cases: List[Case] = current_event_log.cases

    if not cases:
        return {"message": "Dashboard has no current event log cases"}

    results = []

    for case in cases:
        result = case.get_predicted_result()
        if result:
            results.append({
                "case_id": case.id,
                "current_activity": case.get_current_event_activity(),
                "prescription": result
            })

    return {"message": "Success", "results": results}
