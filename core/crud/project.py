import logging

from sqlalchemy.orm import Session

import core.models.project as model
import core.schemas.project as schema
from core.enums.status import ProjectStatus

# Enable logging
logger = logging.getLogger(__name__)


def get_project(db: Session, project_id: int) -> model.Project | None:
    # Get a project by id
    return db.query(model.Project).filter_by(id=project_id).first()


def get_project_by_event_log_id(db: Session, event_log_id: int) -> model.Project | None:
    # Get a project by event log id
    return db.query(model.Project).filter_by(event_log_id=event_log_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> list[model.Project]:
    # Get all projects
    return db.query(model.Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: schema.ProjectCreate, event_log_id: int) -> model.Project:
    # Create a project
    db_project = model.Project(**project.dict(), event_log_id=event_log_id)
    db_project.status = ProjectStatus.PREPROCESSING
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
