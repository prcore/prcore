import logging
import json
from threading import Event
from time import sleep

from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


# Set online inquires
def send_online_inquires() -> bool:
    pass
