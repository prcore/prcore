import logging
from threading import Event
from time import sleep

from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

# Enable logging
logger = logging.getLogger(__name__)

# Set events for consuming
stop_consuming = Event()
consuming_stopped = Event()


def start_consuming(parameters: URLParameters, queue: str, callback_function: callable,
                    prefetch_count: int = 0) -> None:
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    prefetch_count and channel.basic_qos(prefetch_count=prefetch_count)
    channel.basic_consume(queue=queue, on_message_callback=callback_function)

    while not stop_consuming.is_set():
        connection.process_data_events()
        sleep(0.1)

    channel.stop_consuming()
    connection.close()
    consuming_stopped.set()


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)
