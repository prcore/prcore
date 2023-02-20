import logging

from sqlalchemy.orm import Session

import core.models.definition as model
import core.schemas.definition as schema
from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


def create_definition(db: Session, definition: schema.DefinitionCreate) -> model.Definition:
    # Create a definition
    db_definition = model.Definition(**definition.dict())
    db.add(db_definition)
    db.commit()
    db.refresh(db_definition)
    return db_definition


def update_columns_definition(db: Session, definition_id: int,
                              columns_definition: dict[str, ColumnDefinition | None]) -> model.Definition | None:
    # Update a definition's columns definition
    db_definition = db.query(model.Definition).filter_by(id=definition_id).first()

    if db_definition is None:
        return None

    db_definition.columns_definition = columns_definition
    db.commit()
    db.refresh(db_definition)
    return db_definition  # type: ignore


def update_definition(db: Session, definition: schema.Definition) -> model.Definition | None:
    # Update a definition
    db_definition = db.query(model.Definition).filter_by(id=definition.id).first()

    if db_definition is None:
        return None

    db_definition.columns_definition = definition.columns_definition
    db_definition.outcome_definition = definition.outcome_definition
    db_definition.treatment_definition = definition.treatment_definition
    db_definition.fast_mode = definition.fast_mode
    db_definition.start_transition = definition.start_transition
    db_definition.complete_transition = definition.complete_transition
    db.commit()
    db.refresh(db_definition)

    return db_definition  # type: ignore


def set_outcome_treatment_definition(db: Session, db_definition: model.Definition,
                                     outcome: list[list[schema.ProjectDefinition]],
                                     treatment: list[list[schema.ProjectDefinition]],
                                     fast_mode: bool, start_transition: str, complete_transition: str) -> model.Definition:
    # Set outcome and treatment definition
    db_definition.outcome_definition = [[d.dict() for d in data] for data in outcome]
    db_definition.treatment_definition = [[d.dict() for d in data] for data in treatment]
    db_definition.fast_mode = fast_mode
    db_definition.start_transition = start_transition
    db_definition.complete_transition = complete_transition
    db.commit()
    db.refresh(db_definition)
    return db_definition
