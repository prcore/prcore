import logging
import json

from pika import BlockingConnection

from core.confs import config, path
from core.enums.message import MessageType
from core.functions.message.util import get_body
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


def read_training_data(training_data_name) -> dict:
    with open(f"{path.EVENT_LOG_TRAINING_DATA_PATH}/{training_data_name}", "r") as f:
        return json.load(f)
