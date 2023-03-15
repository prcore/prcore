import logging
import json
from datetime import datetime
from time import sleep
from typing import Any, Tuple

from pika import BasicProperties, BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError

from core.enums.message import MessageType
from core.functions.common.etc import get_message_id
from core.starters.rabbitmq import parameters

# Enable logging
logger = logging.getLogger(__name__)


def get_connection(url_parameters: URLParameters) -> BlockingConnection:
    while True:
        try:
            return BlockingConnection(url_parameters)
        except AMQPConnectionError:
            logger.warning("Connection to RabbitMQ failed. Trying again in 5 seconds...")
            sleep(5)


def send_message(receiver_id: str, message_type: MessageType, data: dict) -> bool:
    # Send message to a specific receiver
    result = False
    connection = None

    try:
        connection = get_connection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=receiver_id)
        channel.basic_publish(
            exchange="",
            routing_key=receiver_id,
            body=get_body(message_type, data),
            properties=BasicProperties(message_id=get_message_id())
        )
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
        channel.basic_publish(
            exchange="",
            routing_key=receiver_id,
            body=get_body(message_type, data),
            properties=BasicProperties(message_id=get_message_id())
        )
        result = True
    except Exception as e:
        logger.warning(f"Error while sending message by channel: {e}", exc_info=True)

    return result


def get_body(message_type: MessageType, data: dict) -> bytes:
    result = b""

    try:
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        result = json.dumps({
            "type": message_type,
            "data": data
        }).encode("utf-8")
    except Exception as e:
        logger.warning(f"Error while getting body: {e}", exc_info=True)

    return result


def get_data_from_body(body: bytes) -> Tuple[str, Any]:
    result = ("", None)

    try:
        decoded = json.loads(body.decode("utf-8"))
        result = (decoded["type"], decoded["data"])
    except Exception as e:
        logger.warning(f"Error while getting data from body: {e}", exc_info=True)

    return result
