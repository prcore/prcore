import logging

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

# Enable logging
logger = logging.getLogger(__name__)


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    print(" [x] Received %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)
