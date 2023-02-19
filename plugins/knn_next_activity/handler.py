import logging
from datetime import datetime

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.enums.message import MessageType
from core.functions.common.handler import (handle_online_inquiry, handle_training_data, handle_streaming_prepare,
                                           handle_prescription_request)
from core.functions.message.util import get_data_from_body

from plugins.knn_next_activity.config import basic_info, needed_columns
from plugins.knn_next_activity.initializer import (activate_instance_from_model_file, get_instance_from_model_file,
                                                   preprocess_and_train, deactivate_instance)
from plugins.knn_next_activity import memory

# Enable logging
logger = logging.getLogger(__name__)


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, properties.message_id, data)
    print("-" * 24)

    try:
        message_id = properties.message_id
        if memory.processed_messages.get(message_id):
            return
        else:
            memory.processed_messages[message_id] = datetime.now()
        if message_type == MessageType.ONLINE_INQUIRY:
            handle_online_inquiry(ch, basic_info)
        elif message_type == MessageType.TRAINING_DATA:
            handle_training_data(ch, data, needed_columns, preprocess_and_train)
        elif message_type == MessageType.STREAMING_PREPARE:
            handle_streaming_prepare(ch, data, activate_instance_from_model_file)
        elif message_type == MessageType.PRESCRIPTION_REQUEST:
            instance = get_instance_from_model_file(data["project_id"], data["model_name"])
            handle_prescription_request(ch, data, instance)
        elif message_type == MessageType.STREAMING_STOP:
            deactivate_instance(data["project_id"])
    except Exception as e:
        logger.warning(f"Callback error: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)
