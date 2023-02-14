import logging

from sqlalchemy.orm import Session

import core.models.event_log as model
import core.schemas.event_log as schema

# Enable logging
logger = logging.getLogger(__name__)


def get_event_log(db: Session, event_log_id: int) -> model.EventLog | None:
    # Get an event log by id
    return db.query(model.EventLog).filter_by(id=event_log_id).first()


def get_event_log_by_id(db: Session, event_log_id: int) -> model.EventLog | None:
    # Get an event log by id
    return db.query(model.EventLog).filter_by(id=event_log_id).first()


def get_event_logs(db: Session, skip: int = 0, limit: int = 100) -> list[model.EventLog]:
    # Get all event logs
    return db.query(model.EventLog).offset(skip).limit(limit).all()  # type: ignore


def create_event_log(db: Session, event_log: schema.EventLogCreate) -> model.EventLog:
    # Create an event log
    db_event_log = model.EventLog(**event_log.dict())
    db.add(db_event_log)
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def associate_definition(db: Session, db_event_log: model.EventLog, definition_id: int) -> model.EventLog:
    # Associate a definition to an event log
    db_event_log.definition_id = definition_id
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def set_df_name(db: Session, event_log: model.EventLog, df_name: str) -> model.EventLog:
    # Set dataframe name of an event log
    db_event_log = get_event_log(db, event_log_id=event_log.id)
    if db_event_log:
        db_event_log.df_name = df_name
        db.commit()
        db.refresh(db_event_log)
    return db_event_log


def set_datasets_name(db: Session, event_log: model.EventLog, training_df_name: str,
                      simulation_df_name: str) -> model.EventLog:
    # Set datasets name of an event log
    db_event_log = get_event_log(db, event_log_id=event_log.id)
    if db_event_log:
        db_event_log.training_df_name = training_df_name
        db_event_log.simulation_df_name = simulation_df_name
        db.commit()
        db.refresh(db_event_log)
    return db_event_log
