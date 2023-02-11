import logging

from sqlalchemy.orm import Session

from core.crud.project import set_project_error
from core.functions.event_log.dataset import pre_process_data
from core.functions.message.sender import send_training_data_to_all_plugins
from core.models import event_log as event_log_model


# Enable logging
logger = logging.getLogger(__name__)


def start_pre_processing(project_id: int, db: Session, db_event_log: event_log_model.EventLog) -> bool:
    # Start pre-processing the data
    training_data_name = pre_process_data(db, db_event_log)
    if not training_data_name:
        set_project_error(db, project_id, "Failed to pre-process the data")
        return False
    send_training_data_to_all_plugins(project_id, training_data_name)
    return True
