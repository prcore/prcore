import logging

from sqlalchemy.orm import Session

import core.models.event as model
import core.schemas.event as schema

# Enable logging
logger = logging.getLogger(__name__)


def get_events(db: Session, skip: int = 0, limit: int = 100) -> list[model.Event]:
    # Get all events
    return db.query(model.Event).offset(skip).limit(limit).all()  # type: ignore


def get_event_by_id(db: Session, event_id: int) -> model.Event | None:
    # Get an event by id
    return db.query(model.Event).filter_by(id=event_id).first()


def create_event(db: Session, event: schema.EventCreate, project_id: int, case_id: int) -> model.Event:
    # Create an event
    db_event = model.Event(**event.dict(), project_id=project_id, case_id=case_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int) -> None:
    # Delete an event
    db_event = get_event_by_id(db, event_id=event_id)
    if db_event:
        db.delete(db_event)
        db.commit()
    return db_event
