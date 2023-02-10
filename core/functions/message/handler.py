import logging
from datetime import datetime
from threading import Event
from time import sleep

from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.enums.message import MessageType
from core.functions.message.util import get_data_from_body
from core.starters import memory

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


def callback(ch: BlockingChannel, method: Basic.Deliver, _: BasicProperties, body: bytes) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, data)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    if message_type == MessageType.ONLINE_REPORT.value:
        update_available_plugins(data)


def update_available_plugins(data: dict) -> None:
    memory.available_plugins[data["id"]] = {
        "name": data["name"],
        "prescription_type": data["prescription_type"],
        "description": data["description"],
        "parameters": data["parameters"],
        "online": datetime.now()
    }
    print(memory.available_plugins)