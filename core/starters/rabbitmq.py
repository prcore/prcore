import logging
from urllib.parse import quote

from pika import URLParameters

from core.confs import config

# Enable logging
logger = logging.getLogger("prcore")

# RabbitMQ connection settings
parameters = URLParameters(f"amqp://{config.RABBITMQ_USER}:{quote(config.RABBITMQ_PASS)}"
                           f"@{config.RABBITMQ_HOST}:{config.RABBITMQ_PORT}/%2F")
