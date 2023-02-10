import logging
import json
from threading import Event
from datetime import datetime
from time import sleep

from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.confs import config
from core.enums.message import MessageType
from core.starters import memory
from core.starters.rabbitmq import parameters

# Enable logging
logger = logging.getLogger(__name__)


def send_message(receiver_id: str, message_type: MessageType, data: dict) -> bool:
    # Send message to a specific receiver
    result = False
    connection = None

    try:
        connection = BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=receiver_id)
        channel.basic_publish(exchange="", routing_key=receiver_id, body=get_body(message_type, data))
        result = True
    except Exception as e:
        logger.warning(f"Error while sending message: {e}", exc_info=True)
    finally:
        connection and connection.close()

    return result


def send_message_by_channel(channel: BlockingChannel, receiver_id: str, message_type: MessageType, data: dict) -> bool:
    # Send message to a specific receiver
    result = False

    try:
        channel.queue_declare(queue=receiver_id)
        channel.basic_publish(exchange="", routing_key=receiver_id, body=get_body(message_type, data))
        result = True
    except Exception as e:
        logger.warning(f"Error while sending message by channel: {e}", exc_info=True)

    return result


def get_body(message_type: MessageType, data: dict) -> bytes:
    result = b""

    try:
        result = json.dumps({
            "type": message_type,
            "data": data
        }).encode("utf-8")
    except Exception as e:
        logger.warning(f"Error while getting body: {e}", exc_info=True)

    return result


def get_data_from_body(body: bytes) -> tuple[str, any]:
    result = ("", None)

    try:
        decoded = json.loads(body.decode("utf-8"))
        result = (decoded["type"], decoded["data"])
    except Exception as e:
        logger.warning(f"Error while getting data from body: {e}", exc_info=True)

    return result