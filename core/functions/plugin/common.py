import logging

from pika import BlockingConnection

from core.confs import config
from core.enums.message import MessageType
from core.functions.message.sender import get_body
from core.starters.rabbitmq import parameters

# Enable logging
logger = logging.getLogger(__name__)


def plugin_run(basic_info: dict, callback: callable):
    connection = None
    try:
        connection = BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=config.APP_ID)
        channel.basic_consume(queue=config.APP_ID, on_message_callback=callback)
        channel.basic_publish(exchange="", routing_key="core", body=get_body(MessageType.ONLINE_REPORT, basic_info))
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.warning("Plugin stopped by user")
    finally:
        connection and connection.close()
