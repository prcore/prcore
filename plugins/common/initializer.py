import logging
from typing import Any, Dict, Optional, Type

from core.functions.general.decorator import threaded
from plugins.common import memory
from plugins.common.algorithm import Algorithm
from plugins.common.sender import send_error_report, send_training_start, send_model_name

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def preprocess_and_train(algo: Type[Algorithm], algo_data: Dict[str, Any]) -> None:
    # Pre-process and train the model
    instance = get_instance(algo, algo_data)
    start_training(instance)


def get_instance(algo: Type[Algorithm], algo_data: Dict[str, Any]) -> Algorithm:
    # Get instance from memory
    project_id = algo_data.get("project_id")
    instance = get_instance_from_memory(project_id)
    if instance is not None:
        return instance
    # Get new instance
    instance = get_new_instance(algo, algo_data)
    memory.instances[project_id] = instance
    return instance


def get_instance_from_memory(project_id: int) -> Optional[Algorithm]:
    # Get instance from memory
    if project_id in memory.instances:
        return memory.instances[project_id]
    return None


def get_new_instance(algo: Type[Algorithm], algo_data: Dict[str, Any]) -> Algorithm:
    # Get new instance
    return algo(algo_data)


def activate_instance_from_model_file(algo: Type[Algorithm], algo_data: Dict[str, Any]) -> int:
    # Get instance from model file
    instance = get_instance_from_model_file(algo, algo_data)
    if instance is None:
        return 0
    instance.set_additional_info(algo_data.get("additional_info", {}))
    return instance.get_plugin_id()


def get_instance_from_model_file(algo: Type[Algorithm], algo_data: Dict[str, any]) -> Optional[Algorithm]:
    # Get instance from model file
    result = None

    try:

        project_id = algo_data.get("project_id")
        instance = get_instance_from_memory(project_id)
        if instance is not None:
            return instance
        instance = algo(algo_data)
        instance.load_model()
        memory.instances[project_id] = instance
        result = instance
    except Exception as e:
        logger.warning(f"Failed to load model: {e}", exc_info=True)

    return result


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
