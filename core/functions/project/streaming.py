import asyncio
import logging
import json

from fastapi import Request
from sqlalchemy.orm import Session

import core.crud.event as event_crud
import core.crud.project as project_crud
from core.enums.definition import ColumnDefinition
from core.enums.status import ProjectStatus
from core.functions.project.simulation import simulation_disconnected
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


async def event_generator(request: Request, db: Session, project_id: int):
    try:
        while True:
            if await request.is_disconnected():
                break
            project = project_crud.get_project_by_id(db, project_id)
            if project.status not in {ProjectStatus.SIMULATING, ProjectStatus.STREAMING}:
                break
            data = get_data(db, project_id)
            if data:
                yield {
                    "event": "NEW_RESULT",
                    "id": data[0]["id"],
                    "retry": 15000,
                    "data": json.dumps(data)
                }
            event_ids = [event["id"] for event in data]
            mark_as_sent(db, event_ids)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        memory.reading_projects.discard(project_id)
        simulation_disconnected(db, project_id)


def get_data(db: Session, project_id: int) -> list[dict]:
    # Get data of the SSE stream
    result = []

    try:
        db_events = event_crud.get_events_prescribed_but_not_sent_by_project_id(db, project_id)
        result = [
            {
                "id": event.id,
                "timestamp": event.updated_at.isoformat(),
                "case_completed": event.case.completed,
                "data": {key: value for key, value in event.attributes.items()
                         if key != ColumnDefinition.COMPLETE_INDICATOR},
                "prescriptions": event.prescriptions
            }
            for event in db_events
        ]
    except Exception as e:
        logger.error(f"Error getting data of the SSE stream: {e}")

    return result


def mark_as_sent(db: Session, event_ids: list[int]) -> bool:
    # Mark an event as sent
    result = False

    try:
        event_crud.mark_as_sent_by_event_ids(db, event_ids)
    except Exception as e:
        logger.error(f"Error marking an event as sent: {e}")

    return result
