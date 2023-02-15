import logging

from sqlalchemy.orm import Session

import core.crud.event as event_crud
from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger("prcore")


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
