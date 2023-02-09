import logging
import json

from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.confs import config
from core.enums.message import MessageType
from core.enums.plugin import PluginType
from core.enums.status import PluginStatus
from core.starters.rabbitmq import parameters

# Enable logging
logger = logging.getLogger(__name__)


basic_info = {
    "id": config.APP_TYPE,
    "name": "KNN next activity prediction",
    "prescription_type": PluginType.NEXT_ACTIVITY,
    "description": "This plugin predicts the next activity based on the KNN algorithm.",
    "parameters": {
        "n_neighbors": 3
    }
}


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


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = None
    try:
        connection = BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=config.APP_TYPE)
        channel.basic_consume(queue=config.APP_TYPE, on_message_callback=callback)
        channel.basic_publish(exchange="", routing_key="core", body=get_body(MessageType.ONLINE_REPORT, basic_info))
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.warning("Plugin stopped by user")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
