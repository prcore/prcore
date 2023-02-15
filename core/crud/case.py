import logging

from sqlalchemy.orm import Session

import core.models.case as model
import core.schemas.case as schema

# Enable logging
logger = logging.getLogger("prcore")


def get_cases(db: Session, skip: int = 0, limit: int = 100) -> list[model.Case]:
    # Get all cases
    return db.query(model.Case).offset(skip).limit(limit).all()  # type: ignore


def get_case_by_id(db: Session, case_id: int) -> model.Case | None:
    # Get a case by id
    return db.query(model.Case).filter_by(id=case_id).first()


def get_case_by_project_id_and_case_id(db: Session, project_id: int, case_id: str) -> model.Case | None:
    # Get a case by project id and case id
    return db.query(model.Case).filter_by(project_id=project_id, case_id=case_id).first()


def create_case(db: Session, case: schema.CaseCreate) -> model.Case:
    # Create a case
    db_case = model.Case(**case.dict())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def mark_as_completed(db: Session, db_case: model.Case) -> model.Case | None:
    # Mark a case as completed
    db_case.completed = True
    db.commit()
    db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_id: int) -> None:
    # Delete a case
    db_case = get_case_by_id(db, case_id=case_id)
    if db_case:
        db.delete(db_case)
        db.commit()


def delete_all_cases_by_project_id(db: Session, project_id: int) -> None:
    # Delete cases by project id
    db.query(model.Case).filter_by(project_id=project_id).delete(synchronize_session="fetch")
    db.commit()
