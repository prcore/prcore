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


def get_events_by_case_id_and_project_id(db: Session, case_id: int, project_id: int) -> list[model.Event]:
    # Get all events by case id and project id
    return db.query(model.Event).filter_by(case_id=case_id, project_id=project_id).all()  # type: ignore


def get_events_prescribed_but_not_sent_by_project_id(db: Session, project_id: int) -> list[model.Event]:
    # Get all events prescribed but not sent by project id
    return db.query(model.Event).filter_by(  # type: ignore
        project_id=project_id,
        prescribed=True,
        sent=False
    ).order_by(model.Event.created_at).all()


def create_event(db: Session, event: schema.EventCreate, case_id: int) -> model.Event:
    # Create an event
    db_event = model.Event(**event.dict(), case_id=case_id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def add_prescription(db: Session, db_event: model.Event, plugin_key: str, prescription: dict) -> model.Event:
    # Add a prescription to an event
    db_event.prescriptions = {**db_event.prescriptions, plugin_key: prescription}
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def mark_as_prescribed(db: Session, db_event: model.Event) -> model.Event:
    # Mark an event as prescribed
    db_event.prescribed = True
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def mark_as_sent_by_event_ids(db: Session, event_ids: list[int]) -> None:
    # Mark events as sent by event ids
    db.query(model.Event).filter(model.Event.id.in_(event_ids)).update(  # type: ignore
        {model.Event.sent: True}, synchronize_session="fetch")  # type: ignore
    db.commit()


def delete_event(db: Session, event_id: int) -> None:
    # Delete an event
    db_event = get_event_by_id(db, event_id=event_id)
    if db_event:
        db.delete(db_event)
        db.commit()


def delete_all_events_by_project_id(db: Session, project_id: int) -> None:
    # Delete events by project id
    db.query(model.Event).filter_by(project_id=project_id).delete(synchronize_session="fetch")
    db.commit()
