import logging

from sqlalchemy.orm import Session

import core.models.case as model
import core.schemas.case as schema

# Enable logging
logger = logging.getLogger(__name__)


def get_cases(db: Session, skip: int = 0, limit: int = 100) -> list[model.Case]:
    # Get all cases
    return db.query(model.Case).offset(skip).limit(limit).all()  # type: ignore


def get_case_by_id(db: Session, case_id: int) -> model.Case | None:
    # Get a case by id
    return db.query(model.Case).filter_by(id=case_id).first()


def create_case(db: Session, case: schema.CaseCreate, project_id: int) -> model.Case:
    # Create a case
    db_case = model.Case(**case.dict(), project_id=project_id)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_id: int) -> None:
    # Delete a case
    db_case = get_case_by_id(db, case_id=case_id)
    if db_case:
        db.delete(db_case)
        db.commit()
    return db_case
