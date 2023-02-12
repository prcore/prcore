import logging

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from core.enums.message import MessageType
from core.functions.general.etc import thread
from core.functions.message.util import get_data_from_body, send_message_by_channel
from core.functions.plugin.common import check_training_df, read_training_df

from plugins.knn_next_activity.config import basic_info, needed_columns
from plugins.knn_next_activity.initializer import preprocess_and_train

# Enable logging
logger = logging.getLogger(__name__)


def callback(ch: BlockingChannel, method: Basic.Deliver, _: BasicProperties, body: bytes) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, data)

    try:
        if message_type == MessageType.ONLINE_INQUIRY:
            handle_online_inquiry(ch)
        elif message_type == MessageType.TRAINING_DATA:
            handle_training_data(ch, data)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def handle_online_inquiry(ch: BlockingChannel) -> None:
    send_message_by_channel(ch, "core", MessageType.ONLINE_REPORT, basic_info)


def handle_training_data(ch: BlockingChannel, data: dict) -> bool:
    result = False
    project_id = None

    try:
        project_id = data["project_id"]
        training_df_name = data["training_df_name"]
        training_df = read_training_df(training_df_name)
        applicable = check_training_df(training_df, needed_columns)
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.DATA_REPORT,
            data={"project_id": project_id, "applicable": applicable}
        )
        thread(preprocess_and_train, (project_id, training_df))
    except Exception as e:
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.DATA_REPORT,
            data={"project_id": project_id, "result": "Error while processing data"}
        )
        logger.warning(f"Handle training data failed: {e}")

    return result
