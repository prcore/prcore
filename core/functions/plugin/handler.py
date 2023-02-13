import logging
from typing import Callable

from pika.adapters.blocking_connection import BlockingChannel

from core.enums.message import MessageType
from core.functions.general.etc import thread
from core.functions.message.util import send_message_by_channel
from core.functions.plugin.common import check_training_df, read_training_df

# Enable logging
logger = logging.getLogger(__name__)


def handle_online_inquiry(ch: BlockingChannel, basic_info: dict) -> None:
    send_message_by_channel(ch, "core", MessageType.ONLINE_REPORT, basic_info)


def handle_training_data(ch: BlockingChannel, data: dict, needed_columns: list,
                         preprocess_and_train: Callable) -> bool:
    result = False
    project_id = None

    try:
        project_id = data["project_id"]
        plugin_id = data["plugin_id"]
        training_df_name = data["training_df_name"]
        training_df = read_training_df(training_df_name)
        applicable = check_training_df(training_df, needed_columns)
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.DATA_REPORT,
            data={"project_id": project_id, "plugin_id": plugin_id, "applicable": applicable}
        )
        thread(preprocess_and_train, (project_id, plugin_id, training_df))
    except Exception as e:
        send_message_by_channel(
            channel=ch,
            receiver_id="core",
            message_type=MessageType.DATA_REPORT,
            data={"project_id": project_id, "result": "Error while processing data"}
        )
        logger.warning(f"Handle training data failed: {e}")

    return result


def handle_streaming_prepare(ch: BlockingChannel, data: dict) -> bool:
    pass


def handle_prescription_request(ch: BlockingChannel, data: dict) -> bool:
    pass
