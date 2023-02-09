import logging
from threading import Event
from urllib.parse import quote

from pika import BlockingConnection, URLParameters

from core.confs import config

# Enable logging
logger = logging.getLogger(__name__)

# RabbitMQ connection settings
parameters = URLParameters(f"amqp://{config.RABBITMQ_USER}:{quote(config.RABBITMQ_PASS)}"
                           f"@{config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}/%2F")
stop_consuming = Event()
connection_closed = Event()


def start_consuming(queue: str, callback: callable, prefetch_count: int = 0) -> None:
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    prefetch_count and channel.basic_qos(prefetch_count=prefetch_count)
    channel.basic_consume(queue=queue, on_message_callback=callback)

    while not stop_consuming.is_set():
        connection.process_data_events()

    channel.stop_consuming()
    connection.close()
    connection_closed.set()
