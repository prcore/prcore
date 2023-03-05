import logging

from sqlalchemy.orm import Session

import core.models.definition as model
import core.schemas.definition as schema

# Enable logging
logger = logging.getLogger(__name__)


def create_definition(db: Session, definition: schema.DefinitionCreate) -> model.Definition:
    # Create a definition
    db_definition = model.Definition(**definition.dict())
    db.add(db_definition)
    db.commit()
    db.refresh(db_definition)
    return db_definition


def update_definition(db: Session, definition: schema.Definition) -> model.Definition | None:
    # Update a definition
    db_definition = db.query(model.Definition).filter_by(id=definition.id).first()

    if db_definition is None:
        return None

    db_definition.columns_definition = definition.columns_definition
    db_definition.case_attributes = definition.case_attributes
    db_definition.outcome_definition = definition.outcome_definition
    db_definition.treatment_definition = definition.treatment_definition
    db_definition.fast_mode = definition.fast_mode
    db_definition.start_transition = definition.start_transition
    db_definition.complete_transition = definition.complete_transition
    db_definition.abort_transition = definition.abort_transition
    db.commit()
    db.refresh(db_definition)

    return db_definition  # type: ignore


def set_outcome_treatment_definition(db: Session, db_definition: model.Definition,
                                     outcome: list[list[schema.ProjectDefinition]],
                                     treatment: list[list[schema.ProjectDefinition]]) -> model.Definition:
    # Set outcome and treatment definition
    if outcome:
        db_definition.outcome_definition = [[d.dict() for d in data] for data in outcome]
    if treatment:
        db_definition.treatment_definition = [[d.dict() for d in data] for data in treatment]
    db.commit()
    db.refresh(db_definition)
    return db_definition


def delete_definition_by_id(db: Session, definition_id: int) -> None:
    # Delete a definition by id
    db_definition = db.query(model.Definition).filter_by(id=definition_id).first()
    if not db_definition:
        return
    db.delete(db_definition)
    db.commit()
