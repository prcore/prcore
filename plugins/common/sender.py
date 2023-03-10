import logging

from pika.adapters.blocking_connection import BlockingChannel

from core.confs import config
from core.enums.message import MessageType
from core.functions.message.util import send_message_by_channel, send_message

from plugins.common.algorithm import Algorithm

# Enable logging
logger = logging.getLogger(__name__)


def send_online_report(ch: BlockingChannel, basic_info: dict) -> bool:
    result = False

    try:
        result = send_message_by_channel(ch, "core", MessageType.ONLINE_REPORT, basic_info)
    except Exception as e:
        logger.error(f"Error while sending online report: {e}")

    return result


def send_data_report(ch: BlockingChannel, project_id: int, plugin_id: int, applicable: bool) -> bool:
    return send_message_by_channel(
        channel=ch,
        receiver_id="core",
        message_type=MessageType.DATA_REPORT,
        data={
            "project_id": project_id,
            "plugin_id": plugin_id,
            "applicable": applicable
        }
    )


def send_error_report(project_id: int, plugin_id: int, detail: str) -> bool:
    return send_message(
        receiver_id="core",
        message_type=MessageType.ERROR_REPORT,
        data={
            "project_id": project_id,
            "plugin_id": plugin_id,
            "detail": detail
        }
    )


def send_training_start(instance: Algorithm) -> bool:
    return send_message(
        receiver_id="core",
        message_type=MessageType.TRAINING_START,
        data={
            "project_id": instance.get_project_id(),
            "plugin_id": instance.get_plugin_id()
        }
    )


def send_model_name(instance: Algorithm, model_name: str) -> bool:
    return send_message(
        receiver_id="core",
        message_type=MessageType.MODEL_NAME,
        data={
            "project_id": instance.get_project_id(),
            "plugin_id": instance.get_plugin_id(),
            "model_name": model_name
        }
    )


def send_dataset_prescription_result(ch: BlockingChannel, project_id: int, result_key: int, result: dict) -> bool:
    return send_message_by_channel(
        channel=ch,
        receiver_id="core",
        message_type=MessageType.DATASET_PRESCRIPTION_RESULT,
        data={"project_id": project_id, "plugin_key": config.APP_ID, "result_key": result_key, "data": result}
    )


def send_streaming_ready(ch: BlockingChannel, project_id: int, plugin_id: int) -> bool:
    return send_message_by_channel(
        channel=ch,
        receiver_id="core",
        message_type=MessageType.STREAMING_READY,
        data={"project_id": project_id, "plugin_id": plugin_id}
    )


def send_streaming_prescription_result(ch: BlockingChannel, project_id: int, event_id: int, result: dict) -> bool:
    return send_message_by_channel(
        channel=ch,
        receiver_id="core",
        message_type=MessageType.STREAMING_PRESCRIPTION_RESULT,
        data={"project_id": project_id, "plugin_key": config.APP_ID, "event_id": event_id, "data": result}
    )
