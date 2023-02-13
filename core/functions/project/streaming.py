import logging

from sqlalchemy.orm import Session

# Enable logging
logger = logging.getLogger(__name__)


# def get_event(db: Session, project_id: int) -> model.Event | None:
#     # Get an event by project id
#     return db.query(model.Event).filter_by(project_id=project_id).first()
#
