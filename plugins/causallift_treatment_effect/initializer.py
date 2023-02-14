import logging
from typing import Optional

from pandas import DataFrame

from core.functions.plugin.common import start_training

from plugins.causallift_treatment_effect import memory
from plugins.causallift_treatment_effect.algorithm import Algorithm

# Enable logging
logger = logging.getLogger(__name__)


def get_instance(project_id: int, plugin_id: int, training_df: DataFrame, treatment_definition: list) -> Algorithm:
    # Get instance from memory
    instance = get_instance_from_memory(project_id)
    if instance is not None:
        return instance
    # Get new instance
    instance = get_new_instance(project_id, plugin_id, training_df, treatment_definition)
    memory.instances[project_id] = instance
    return instance


def get_instance_from_memory(project_id: int) -> Optional[Algorithm]:
    # Get instance from memory
    if project_id in memory.instances:
        return memory.instances[project_id]
    return None


def get_instance_from_model_file(project_id: int, model_name: str) -> Optional[Algorithm]:
    instance = get_instance_from_memory(project_id)
    if instance is None:
        instance = Algorithm(project_id, None, None, model_name)
    instance.load_model()
    memory.instances[project_id] = instance
    return instance


def get_new_instance(project_id: int, plugin_id: int, training_df: DataFrame, treatment_definition: list) -> Algorithm:
    # Get new instance
    return Algorithm(
        project_id=project_id,
        plugin_id=plugin_id,
        df=training_df,
        treatment_definition=treatment_definition
    )


def activate_instance_from_model_file(project_id: int, model_name: str) -> int:
    # Get instance from model file
    instance = get_instance_from_model_file(project_id, model_name)
    return instance.get_plugin_id()


def preprocess_and_train(project_id: int, plugin_id: int, training_df: DataFrame,
                         treatment_definition: list) -> None:
    # Pre-process and train the model
    instance = get_instance(project_id, plugin_id, training_df, treatment_definition)
    start_training(instance)


def deactivate_instance(project_id: int) -> None:
    # Deactivate instance
    if project_id in memory.instances:
        del memory.instances[project_id]