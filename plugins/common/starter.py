import logging
from time import sleep
from typing import Any, Dict, Type

from apscheduler.schedulers.background import BackgroundScheduler
from pika import BasicProperties
from pika.exceptions import ConnectionClosedByBroker
from tzlocal import get_localzone

from core.confs import config
from core.enums.message import MessageType
from core.functions.common.timer import log_rotation, processed_messages_clean
from core.functions.common.etc import get_message_id
from core.functions.message.util import get_connection, get_body
from core.starters.rabbitmq import parameters

from plugins.common import memory
from plugins.common.algorithm import Algorithm
from plugins.common.handler import callback
from plugins.common.sender import send_online_report

# Enable logging
logger = logging.getLogger(__name__)


def plugin_scheduler(basic_info: dict) -> None:
    # Start the scheduler
    scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 300}, timezone=str(get_localzone()))
    scheduler.add_job(log_rotation, "cron", hour=23, minute=59)
    scheduler.add_job(processed_messages_clean, "interval", [memory.processed_messages], minutes=5)
    scheduler.add_job(send_online_report, "interval", [basic_info], minutes=14)
    scheduler.start()


def plugin_run(algo: Type[Algorithm], basic_info: Dict[str, Any], prefetch_count: int = 0) -> None:
    # Start the rabbitmq connection
    connection = None
    try:
        connection = get_connection(parameters)
        logger.warning("Connection to RabbitMQ established")
        channel = connection.channel()
        channel.queue_declare(queue=config.APP_ID)
        prefetch_count and channel.basic_qos(prefetch_count=prefetch_count)
        channel.basic_consume(
            queue=config.APP_ID,
            on_message_callback=lambda ch, method, properties, body: callback(
                ch=ch,
                method=method,
                properties=properties,
                body=body,
                algo=algo,
                basic_info=basic_info
            )
        )
        channel.basic_publish(
            exchange="",
            routing_key="core",
            body=get_body(MessageType.ONLINE_REPORT, basic_info),
            properties=BasicProperties(message_id=get_message_id())
        )
        try:
            channel.start_consuming()
        except ConnectionClosedByBroker:
            logger.warning("Connection to RabbitMQ closed by broker. Trying again in 5 seconds...")
            sleep(5)
            return plugin_run(algo, basic_info, prefetch_count)
    except KeyboardInterrupt:
        logger.warning("Plugin stopped by user")
    finally:
        if connection and connection.is_open:
            connection.close()
