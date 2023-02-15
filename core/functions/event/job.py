import logging

from pandas import to_datetime

from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_start_timestamp
from core.functions.message.sender import send_prescription_request_to_all_plugins
from core.functions.plugin.collector import get_active_plugins

# Enable logging
logger = logging.getLogger(__name__)


def prepare_prefix_and_send(project_id: int, model_names: dict[str, str], event_id: int,
                            columns_definition: dict[str, ColumnDefinition], data: list[dict]) -> bool:
    # Prepare prefix and send to all plugins
    result = False

    try:
        # Rename columns of elements in data list based on definition
        for element in data:
            for column in list(element):
                if column in columns_definition:
                    element[columns_definition[column]] = element.pop(column)

        # Get timestamp column
        timestamp_column = columns_definition[get_start_timestamp(columns_definition)]

        # Sort data's element by timestamp
        data.sort(key=lambda x: to_datetime(x[timestamp_column]))
        send_prescription_request_to_all_plugins(project_id, list(get_active_plugins()), model_names, event_id, data)
        result = True
    except Exception as e:
        logger.error(f"Error while preparing prefix and sending to plugins: {e}", exc_info=True)

    return result
