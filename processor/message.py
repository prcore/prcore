import logging
from datetime import datetime

from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

import core.schemas.definition as definition_schema
from core.confs import path
from core.enums.message import MessageType
from core.functions.common.file import delete_file, get_dataframe_from_pickle, get_new_path, save_dataframe_to_pickle
from core.functions.message.util import get_data_from_body, send_message
from processor import memory
from processor.dataset import get_processed_dataframe

# Enable logging
logger = logging.getLogger(__name__)


def callback(ch: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
    message_type, data = get_data_from_body(body)
    print(message_type, properties.message_id, data)
    print("-" * 24)

    try:
        message_id = properties.message_id
        if memory.processed_messages.get(message_id):
            return
        else:
            memory.processed_messages[message_id] = datetime.now()
        if message_type == MessageType.PROCESS_REQUEST:
            handle_process_request(data)
    except Exception as e:
        logger.warning(f"Callback error: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def handle_process_request(data: dict) -> None:
    request_key = data["request_key"]
    df_name = data["df_name"]
    definition = definition_schema.Definition(**data["definition"])
    memory.pending_dfs[request_key] = {
        "date": datetime.now(),
        "df_name": df_name
    }
    original_df_path = f"{path.TEMP_PATH}/{df_name}"
    original_df = get_dataframe_from_pickle(original_df_path)
    delete_file(original_df_path)
    if original_df is None:
        return send_process_result(request_key)
    processed_df = get_processed_dataframe(original_df, definition)
    if processed_df is None:
        return send_process_result(request_key)
    temp_path = get_new_path(f"{path.TEMP_PATH}/", suffix=".pkl")
    save_dataframe_to_pickle(temp_path, processed_df)
    memory.pending_dfs[request_key]["processed_df"] = temp_path.split("/")[-1]
    used_time = (datetime.now() - memory.pending_dfs[request_key]["date"]).total_seconds()
    memory.pending_dfs[request_key]["used_time"] = round(used_time, 1)
    send_process_result(request_key)


def send_process_result(request_key: str) -> None:
    send_message(
        receiver_id="core",
        message_type=MessageType.PROCESS_RESULT,
        data={
            "request_key": request_key,
            "df_name": memory.pending_dfs[request_key]["df_name"],
            "processed_df": memory.pending_dfs[request_key].get("processed_df"),
            "used_time": memory.pending_dfs[request_key].get("used_time")
        }
    )
    memory.pending_dfs.pop(request_key)
