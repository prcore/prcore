import logging

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.confs import config
from core.enums.message import MessageType
from core.enums.plugin import PluginType
from core.functions.message.handler import get_data_from_body
from core.functions.message.sender import send_message
from core.functions.plugin.common import plugin_run

# Enable logging
logger = logging.getLogger(__name__)


basic_info = {
    "id": config.APP_ID,
    "name": "KNN next activity prediction",
    "prescription_type": PluginType.NEXT_ACTIVITY,
    "description": "This plugin predicts the next activity based on the KNN algorithm.",
    "parameters": {
        "n_neighbors": 3
    }
}


def callback(ch: BlockingChannel, method: Basic.Deliver, _: BasicProperties, body: bytes) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, data)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    if message_type == MessageType.ONLINE_INQUIRY.value:
        send_message("core", MessageType.ONLINE_REPORT, basic_info)


if __name__ == "__main__":
    plugin_run(basic_info, callback)
