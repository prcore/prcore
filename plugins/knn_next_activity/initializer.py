import logging

from pandas import DataFrame

from core.enums.message import MessageType
from core.functions.message.util import send_message

from plugins.knn_next_activity import memory
from plugins.knn_next_activity.algorithm import Algorithm

# Enable logging
logger = logging.getLogger(__name__)


def get_instance(project_id: int, training_df: DataFrame) -> Algorithm:
    # Get instance from memory
    if project_id in memory.instances:
        return memory.instances[project_id]
    # Get new instance
    instance = get_new_instance(project_id, training_df)
    memory.instances[project_id] = instance
    return instance


def get_new_instance(project_id: int, training_df: DataFrame) -> Algorithm:
    # Get new instance
    return Algorithm(project_id, training_df)


def preprocess_and_train(project_id: int, training_df: DataFrame) -> None:
    # Pre-process and train the model
    instance = get_instance(project_id, training_df)
    preprocess_result = instance.preprocess()
    if not preprocess_result:
        send_message("core", MessageType.ERROR_REPORT, {"project_id": project_id, "detail": "Pre-process failed"})
    else:
        send_message("core", MessageType.TRAINING_START, {"project_id": project_id})
    train_result = instance.train()
    if not train_result:
        send_message("core", MessageType.ERROR_REPORT, {"project_id": project_id, "detail": "Train failed"})
    model_name = instance.save_model()
    if not model_name:
        send_message("core", MessageType.ERROR_REPORT, {"project_id": project_id, "detail": "Save model failed"})
    else:
        send_message("core", MessageType.MODEL_NAME, {"project_id": project_id, "model_name": model_name})
