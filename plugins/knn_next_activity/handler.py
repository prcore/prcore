import logging

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.enums.message import MessageType
from core.functions.message.util import get_data_from_body
from core.functions.plugin.handler import handle_online_inquiry, handle_training_data

from plugins.knn_next_activity.config import basic_info, needed_columns
from plugins.knn_next_activity.initializer import preprocess_and_train

# Enable logging
logger = logging.getLogger(__name__)


def callback(ch: BlockingChannel, method: Basic.Deliver, _: BasicProperties, body: bytes) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, data)

    try:
        if message_type == MessageType.ONLINE_INQUIRY:
            handle_online_inquiry(ch, basic_info)
        elif message_type == MessageType.TRAINING_DATA:
            handle_training_data(ch, data, needed_columns, preprocess_and_train)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)
