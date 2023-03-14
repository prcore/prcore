import logging
from typing import Any

from pandas import to_datetime

from core.enums.definition import ColumnDefinition, DefinitionType
from core.functions.definition.util import get_start_timestamp, get_column_definition
from core.functions.message.sender import send_streaming_prescription_request_to_all_plugins

# Enable logging
logger = logging.getLogger(__name__)


def prepare_prefix_and_send(project_id: int, model_names: dict[str, str], event_id: int,
                            columns_definition: dict[str, ColumnDefinition], case_attributes: list[str],
                            data: list[dict], additional_infos: dict[str, dict[str, Any]]) -> bool:
    # Prepare prefix and send to all plugins
    result = False

    try:
        # Rename columns
        data = rename_elements(data, columns_definition, case_attributes)

        # Get timestamp column
        timestamp_column = columns_definition[get_start_timestamp(columns_definition)]

        # Sort data's element by timestamp
        data.sort(key=lambda x: to_datetime(x[timestamp_column]))
        send_streaming_prescription_request_to_all_plugins(
            plugins=list(model_names.keys()),
            project_id=project_id,
            model_names=model_names,
            event_id=event_id,
            prefix=data,
            additional_infos=additional_infos
        )
        result = True
    except Exception as e:
        logger.error(f"Error while preparing prefix and sending to plugins: {e}", exc_info=True)

    return result


def rename_elements(data: list[dict], columns_definition: dict[str, ColumnDefinition],
                    case_attributes: list[str]) -> list[dict]:
    # Rename columns of elements in data list based on definition
    for element in data:
        for column in list(element):
            definition = get_column_definition(column, columns_definition)
            if definition in DefinitionType.SPECIAL:
                element[definition] = element.pop(column)
            elif definition == ColumnDefinition.CATEGORICAL:
                element[f"CATEGORICAL_{column}"] = element.pop(column)
            elif case_attributes and column in case_attributes:
                element[f"CASE_ATTRIBUTE_{definition}_{column}"] = element.pop(column)
            else:
                element[f"EVENT_ATTRIBUTE_{definition}_{column}"] = element.pop(column)
    return data
