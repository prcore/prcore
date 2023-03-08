import logging
from typing import Any, Dict, Optional, Type

from pandas import DataFrame

from core.functions.general.decorator import threaded
from plugins.common import memory
from plugins.common.algorithm import Algorithm
from plugins.common.sender import send_error_report, send_training_start, send_model_name

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def preprocess_and_train(algo: Type[Algorithm], basic_info: Dict[str, Any], project_id: int, plugin_id: int,
                         training_df: DataFrame, treatment_definition: list) -> None:
    # Pre-process and train the model
    instance = get_instance(algo, basic_info, project_id, plugin_id, training_df, treatment_definition)
    start_training(instance)


def get_instance(algo: Type[Algorithm], basic_info: Dict[str, Any], project_id: int, plugin_id: int,
                 training_df: DataFrame, treatment_definition: list) -> Algorithm:
    # Get instance from memory
    instance = get_instance_from_memory(project_id)
    if instance is not None:
        return instance
    # Get new instance
    instance = get_new_instance(algo, basic_info, project_id, plugin_id, training_df, treatment_definition)
    memory.instances[project_id] = instance
    return instance


def get_instance_from_memory(project_id: int) -> Optional[Algorithm]:
    # Get instance from memory
    if project_id in memory.instances:
        return memory.instances[project_id]
    return None


def get_new_instance(algo: Type[Algorithm], basic_info: Dict[str, Any], project_id: int, plugin_id: int,
                     training_df: DataFrame, treatment_definition: list) -> Algorithm:
    # Get new instance
    return algo(
        basic_info=basic_info,
        project_id=project_id,
        plugin_id=plugin_id,
        df=training_df,
        treatment_definition=treatment_definition
    )


def activate_instance_from_model_file(algo: Type[Algorithm], basic_info: Dict[str, Any], project_id: int,
                                      model_name: str) -> int:
    # Get instance from model file
    instance = get_instance_from_model_file(algo, basic_info, project_id, model_name)
    return instance.get_plugin_id()


def get_instance_from_model_file(algo: Type[Algorithm], basic_info: Dict[str, Any], project_id: int,
                                 model_name: str) -> Optional[Algorithm]:
    instance = get_instance_from_memory(project_id)
    if instance is None:
        instance = algo(
            basic_info=basic_info,
            project_id=project_id,
            model_name=model_name
        )
    instance.load_model()
    memory.instances[project_id] = instance
    return instance


def deactivate_instance(project_id: int) -> None:
    # Deactivate instance
    if project_id in memory.instances:
        del memory.instances[project_id]


def start_training(instance: Algorithm) -> None:
    try:
        preprocess_error = instance.preprocess()
    except Exception as e:
        logger.warning(f"Pre-processing failed: {e}", exc_info=True)
        preprocess_error = str(e)
    if preprocess_error:
        send_error_report(instance.get_project_id(), instance.get_plugin_id(),
                          f"Pre-processing failed: {preprocess_error}")
        return

    send_training_start(instance)
    try:
        train_error = instance.train()
    except Exception as e:
        logger.warning(f"Training failed: {e}", exc_info=True)
        train_error = str(e)
    if train_error:
        send_error_report(instance.get_project_id(), instance.get_plugin_id(), f"Training failed: {train_error}")
        return

    model_name = instance.save_model()
    if not model_name:
        send_error_report(instance.get_project_id(), instance.get_plugin_id(), "Saving model failed")
        return
    send_model_name(instance, model_name)
