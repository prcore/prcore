import logging

from plugins.knn_next_activity import memory
from plugins.knn_next_activity.algorithm import Algorithm

# Enable logging
logger = logging.getLogger(__name__)


def get_instance(project_id: int, training_data_name: str) -> Algorithm:
    # Get instance from memory
    if project_id in memory.instances:
        return memory.instances[project_id]
    # Get new instance
    instance = get_new_instance(project_id, training_data_name)
    memory.instances[project_id] = instance
    return instance


def get_new_instance(project_id: int, training_data_name: str) -> Algorithm:
    # Get new instance
    return Algorithm(project_id)

