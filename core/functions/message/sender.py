import logging
import json
from threading import Event
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


def send_message(plugin_id: str, message_type: MessageType, data: dict) -> bool:
    # Send message to a specific plugin
    result = False
    connection = None

    try:
        connection = BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=plugin_id)
        channel.basic_publish(exchange="", routing_key=plugin_id, body=get_body(message_type, data))
        result = True
    except Exception as e:
        logger.warning(f"Error while sending message: {e}", exc_info=True)
    finally:
        connection and connection.close()

    return result


def send_online_inquires() -> bool:
    # Send online inquiries to all plugins
    return bool(all(send_online_inquiry(plugin_id)
                    for plugin_id in config.ENABLED_PLUGINS.split("||")))


def send_online_inquiry(plugin_id: str) -> bool:
    # Send online inquiry to a specific plugin
    return send_message(plugin_id, MessageType.ONLINE_INQUIRY, {})


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
