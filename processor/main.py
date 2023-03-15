import logging
from time import sleep

from apscheduler.schedulers.background import BackgroundScheduler
from pika.exceptions import ConnectionClosedByBroker
from tzlocal import get_localzone

from core.confs import config
from core.functions.common.timer import log_rotation, processed_messages_clean
from core.functions.message.util import get_connection
from core.starters.rabbitmq import parameters
from processor import memory
from processor.message import callback

# Enable logging
logger = logging.getLogger(__name__)


def processor_scheduler() -> None:
    # Start the scheduler
    scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 300}, timezone=str(get_localzone()))
    scheduler.add_job(log_rotation, "cron", hour=23, minute=59)
    scheduler.add_job(processed_messages_clean, "interval", [memory.processed_messages], minutes=5)
    scheduler.start()


def processor_run() -> None:
    # Start the rabbitmq connection
    connection = None
    try:
        connection = get_connection(parameters)
        logger.warning("Connection to RabbitMQ established")
        channel = connection.channel()
        channel.queue_declare(queue=config.APP_ID)
        channel.basic_consume(queue=config.APP_ID, on_message_callback=callback)
        try:
            channel.start_consuming()
        except ConnectionClosedByBroker:
            logger.warning("Connection to RabbitMQ closed by broker. Trying again in 5 seconds...")
            sleep(5)
            return processor_run()
    except KeyboardInterrupt:
        logger.warning("Processor stopped by user")
    finally:
        if connection and connection.is_open:
            connection.close()


if __name__ == "__main__":
    processor_scheduler()
    processor_run()
