import logging

from fastapi import APIRouter

from blupee import glovar
from blupee.models import CurrentEventLog

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

    if not (cases := current_event_log.cases):
        return {"message": "Dashboard has no current event log cases"}

    results = []

    for case in cases:
        if result := case.get_predicted_result():
            results.append({
                "case_id": case.id,
                "prescription": result
            })

    return {"message": "Success", "results": results}
