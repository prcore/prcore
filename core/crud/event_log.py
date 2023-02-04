import logging

from sqlalchemy.orm import Session

import core.models.event_log as model
import core.schemas.event_log as schema

# Enable logging
logger = logging.getLogger(__name__)


def get_event_log(db: Session, event_log_id: int) -> model.EventLog | None:
    # Get an event log by id
    return db.query(model.EventLog).filter_by(id=event_log_id).first()


def get_event_logs(db: Session, skip: int = 0, limit: int = 100) -> list[model.EventLog]:
    # Get all event logs
    return db.query(model.EventLog).offset(skip).limit(limit).all()


def create_event_log(db: Session, event_log: schema.EventLogCreate) -> model.EventLog:
    # Create an event log
    db_event_log = model.EventLog(**event_log.dict())
    db.add(db_event_log)
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def update_event_log(db: Session, event_log_id: int, definition_id: int) -> model.EventLog:
    # Update an event log
    db_event_log = get_event_log(db, event_log_id=event_log_id)
    if db_event_log:
        db_event_log.definition_id = definition_id
        db.commit()
        db.refresh(db_event_log)
    return db_event_log
