import logging
from datetime import datetime

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


def update_definition(db: Session, definition: schema.Definition) -> model.Definition:
    # Update a definition
    db_definition = db.query(model.Definition).filter(model.Definition.id == definition.id).first()
    db_definition.columns_definition = definition.columns_definition
    db_definition.outcome_definition = definition.outcome_definition
    db_definition.treatment_definition = definition.treatment_definition
    db.commit()
    db.refresh(db_definition)
    return db_definition
