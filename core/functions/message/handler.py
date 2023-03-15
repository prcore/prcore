import logging
from datetime import datetime
from threading import Event
from time import sleep

from pika import URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import ConnectionClosedByBroker
from pika.spec import Basic, BasicProperties
from sqlalchemy.orm import Session

import core.crud.event as event_crud
import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
from core.starters.database import SessionLocal
from core.enums.message import MessageType
from core.enums.status import PluginStatus, ProjectStatus
from core.functions.message.sender import send_online_inquires
from core.functions.message.util import get_connection, get_data_from_body
from core.functions.plugin.util import is_plugin_active
from core.functions.project.streaming import enable_streaming, check_simulation
from core.functions.project.util import get_project_status
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)

# Set events for consuming
stop_consuming = Event()
consuming_stopped = Event()


def start_consuming(parameters: URLParameters, queue: str, callback_function: callable,
                    prefetch_count: int = 0) -> None:
    connection = get_connection(parameters)
    logger.warning("Connection to RabbitMQ established")
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    prefetch_count and channel.basic_qos(prefetch_count=prefetch_count)
    channel.basic_consume(queue=queue, on_message_callback=callback_function)
    send_online_inquires()

    while not stop_consuming.is_set():
        try:
            connection.process_data_events()
        except ConnectionClosedByBroker:
            logger.warning("Connection to RabbitMQ closed by broker. Trying again in 5 seconds...")
            sleep(5)
            return start_consuming(parameters, queue, callback_function, prefetch_count)
        sleep(0.1)

    channel.stop_consuming()
    connection.close()
    consuming_stopped.set()


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
        if message_type == MessageType.ONLINE_REPORT:
            handle_online_report(data)
        elif message_type == MessageType.DATA_REPORT:
            handle_data_report(data)
        elif message_type == MessageType.ERROR_REPORT:
            handle_error_report(data)
        elif message_type == MessageType.TRAINING_START:
            handle_training_start(data)
        elif message_type == MessageType.MODEL_NAME:
            handle_model_name(data)
        elif message_type == MessageType.DATASET_PRESCRIPTION_RESULT:
            handle_dataset_prescription_result(data)
        elif message_type == MessageType.STREAMING_READY:
            handle_streaming_ready(data)
        elif message_type == MessageType.STREAMING_PRESCRIPTION_RESULT:
            handle_streaming_prescription_result(data)
        elif message_type == MessageType.PROCESS_RESULT:
            handle_process_result(data)
    except Exception as e:
        logger.error(f"Error while handling message {message_type}: {e}", exc_info=True)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def handle_online_report(data: dict) -> None:
    memory.available_plugins[data["id"]] = {
        "prescription_type": data.get("prescription_type", "Unknown"),
        "name": data.get("name", "Plugin"),
        "description": data.get("description", "No description"),
        "parameters": data.get("parameters", {}),
        "needed_columns": data.get("needed_columns", []),
        "needed_info_for_training": data.get("needed_info_for_training", []),
        "needed_info_for_prediction": data.get("needed_info_for_prediction", []),
        "supported_encoding": data.get("supported_encoding", []),
        "online": datetime.now()
    }


def handle_data_report(data: dict) -> None:
    project_id = data["project_id"]
    plugin_id = data["plugin_id"]
    applicable = data["applicable"]
    with SessionLocal() as db:
        plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
        if not plugin:
            return
        if applicable:
            plugin_crud.update_status(db, plugin, PluginStatus.PREPROCESSING)
            update_project_status(db, project_id)
        else:
            plugin_crud.delete_plugin(db, plugin)
            db_project = project_crud.get_project_by_id(db, project_id)
            if not db_project:
                return
            if not db_project.plugins:
                project_crud.set_project_error(db, db_project, "No plugin is applicable")


def handle_error_report(data: dict) -> None:
    project_id = data["project_id"]
    plugin_id = data["plugin_id"]
    detail = data["detail"]
    with SessionLocal() as db:
        plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
        if not plugin:
            return
        plugin_crud.set_plugin_error(db, plugin, detail)
        update_project_status(db, project_id)


def handle_training_start(data: dict) -> None:
    project_id = data["project_id"]
    plugin_id = data["plugin_id"]
    with SessionLocal() as db:
        plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
        if not plugin:
            return
        plugin_crud.update_status(db, plugin, PluginStatus.TRAINING)
        update_project_status(db, project_id)


def handle_model_name(data: dict) -> None:
    project_id = data["project_id"]
    plugin_id = data["plugin_id"]
    model_name = data["model_name"]
    with SessionLocal() as db:
        plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
        if not plugin:
            return
        plugin_crud.update_status(db, plugin, PluginStatus.TRAINED)
        plugin_crud.update_model_name(db, plugin, model_name)
        update_project_status(db, project_id)


def handle_dataset_prescription_result(data: dict) -> None:
    project_id = data["project_id"]
    plugin_key = data["plugin_key"]
    result_key = data["result_key"]
    prescriptions = data["data"]
    if result_key not in memory.ongoing_results:
        return
    memory.ongoing_results[result_key]["results"][plugin_key] = prescriptions
    with SessionLocal() as db:
        db_project = project_crud.get_project_by_id(db, project_id)
        if not db_project:
            return


def handle_streaming_ready(data: dict) -> None:
    project_id = data["project_id"]
    plugin_id = data["plugin_id"]
    with SessionLocal() as db:
        plugin = plugin_crud.get_plugin_by_id(db, plugin_id)
        if not plugin:
            return
        plugin_crud.update_status(db, plugin, PluginStatus.STREAMING)
        enable_streaming(db, project_id)


def handle_streaming_prescription_result(data: dict) -> None:
    project_id = data["project_id"]
    plugin_key = data["plugin_key"]
    event_id = data["event_id"]
    result = data["data"]
    with SessionLocal() as db:
        db_project = project_crud.get_project_by_id(db, project_id)
        if not db_project or db_project.status not in {ProjectStatus.STREAMING, ProjectStatus.SIMULATING}:
            return
        event = event_crud.get_event_by_id(db, event_id)
        if not event:
            return
        event = event_crud.add_prescription(db, event, plugin_key, result)
        # Check if all plugins have finished
        if all([event.prescriptions.get(plugin.key) for plugin in db_project.plugins
                if is_plugin_active(plugin.key) and plugin.status == PluginStatus.STREAMING]):
            event_crud.mark_as_prescribed(db, event)
        # Check if the simulation is finished
        check_simulation(db, db_project)


def handle_process_result(data: dict) -> None:
    request_key = data["request_key"]
    df_name = data["df_name"]
    processed_df = data.get("processed_df")
    if request_key not in memory.pending_dfs:
        return
    if df_name != memory.pending_dfs[request_key]["df_name"]:
        return
    memory.pending_dfs[request_key]["processed_df"] = processed_df
    memory.pending_dfs[request_key]["finished"] = True


def update_project_status(db: Session, project_id: int) -> None:
    project = project_crud.get_project_by_id(db, project_id)
    if not project:
        return
    project_status = get_project_status([plugin.status for plugin in project.plugins])
    if project_status == ProjectStatus.ERROR:
        project_crud.set_project_error(db, project, "Plugins encountered errors")
    elif project_status and project_status != project.status:
        project_crud.update_status(db, project, project_status)
