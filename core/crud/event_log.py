import logging

from sqlalchemy.orm import Session

import core.models.event_log as model
import core.schemas.event_log as schema
import core.models.project as project_model

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


def get_all_event_logs_without_associated_project(db: Session) -> list[model.EventLog]:
    # Get all event logs without associated project
    subquery = db.query(project_model.Project.event_log_id).distinct().subquery()
    return db.query(model.EventLog).filter(~model.EventLog.id.in_(subquery.select())).all()  # type: ignore


def get_all_saved_names(db: Session) -> list[str]:
    # Get all saved names
    return [x[0] for x in db.query(model.EventLog.saved_name).all()]


def get_all_df_names(db: Session) -> list[str]:
    # Get all dataframe names
    return [x[0] for x in db.query(model.EventLog.df_name).all()]


def get_all_training_df_names(db: Session) -> list[str]:
    # Get all training dataframe names
    return [x[0] for x in db.query(model.EventLog.training_df_name).all()]


def get_all_simulation_df_names(db: Session) -> list[str]:
    # Get all simulation dataframe names
    return [x[0] for x in db.query(model.EventLog.simulation_df_name).all()]


def create_event_log(db: Session, event_log: schema.EventLogCreate) -> model.EventLog:
    # Create an event log
    db_event_log = model.EventLog(**event_log.dict())
    db.add(db_event_log)
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def update_event_log(db: Session, db_event_log: model.EventLog, file_name: str, saved_name: str) -> model.EventLog:
    # Update an event log
    db_event_log.file_name = file_name
    db_event_log.saved_name = saved_name
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def associate_definition(db: Session, db_event_log: model.EventLog, definition_id: int) -> model.EventLog:
    # Associate a definition to an event log
    db_event_log.definition_id = definition_id
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def set_df_name(db: Session, db_event_log: model.EventLog, df_name: str) -> model.EventLog:
    # Set dataframe name of an event log
    db_event_log.df_name = df_name
    db.commit()
    db.refresh(db_event_log)
    return db_event_log


def set_datasets_name(db: Session, event_log_id: int, training_df_name: str, simulation_df_name: str) -> model.EventLog:
    # Set datasets name of an event log
    db_event_log = get_event_log(db, event_log_id=event_log_id)
    if db_event_log:
        db_event_log.training_df_name = training_df_name
        db_event_log.simulation_df_name = simulation_df_name
        db.commit()
        db.refresh(db_event_log)
    return db_event_log


def delete_event_log_by_id(db: Session, event_log_id: int) -> None:
    # Delete an event log by id
    db_event_log = get_event_log(db, event_log_id=event_log_id)
    if not db_event_log:
        return
    db.delete(db_event_log)
    db.commit()
