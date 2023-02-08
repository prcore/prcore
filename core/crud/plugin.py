import logging

from sqlalchemy.orm import Session

import core.models.plugin as model

# Enable logging
logger = logging.getLogger(__name__)


def get_plugins(db: Session, skip: int = 0, limit: int = 100) -> list[model.Plugin]:
    # Get all plugins
    return db.query(model.Plugin).offset(skip).limit(limit).all()
