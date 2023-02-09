import logging
from urllib.parse import quote

import pika

from core.confs import config

# Enable logging
logger = logging.getLogger(__name__)

parameters = pika.URLParameters(f"amqp://{config.RABBITMQ_USER}:{quote(config.RABBITMQ_PASS)}"
                                f"@{config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}/%2F")
connection = pika.BlockingConnection(parameters)


def start_consuming(conn: pika.BlockingConnection, queue: str, callback: callable,
                    prefetch_count: int = 0) -> None:
    channel = conn.channel()
    channel.queue_declare(queue=queue)
    prefetch_count and channel.basic_qos(prefetch_count=prefetch_count)
    channel.basic_consume(queue=queue, on_message_callback=callback)
    channel.start_consuming()
    conn.close()
