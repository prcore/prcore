import logging

from pandas import DataFrame

from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_defined_column_name

# Enable logging
logger = logging.getLogger(__name__)


def get_brief_with_inferred_definition(df: DataFrame) -> list[list[str | int | float | bool | ColumnDefinition | None]]:
    # Get brief with inferred definition
    result = []

    try:
        result: list = df.head(5).values.tolist()  # type: ignore
        header = df.columns.tolist()
        result.insert(0, header)
        result.insert(1, get_inferred_definitions(header))
    except Exception as e:
        logger.warning(f"Get brief with inferred definition error: {e}", exc_info=True)

    return result


def get_inferred_definitions(header: list[str]) -> list[ColumnDefinition | None]:
    # Get inferred definition
    result = []

    try:
        result = [get_inferred_definition_by_name(header) for header in header]
    except Exception as e:
        logger.warning(f"Get inferred definition error: {e}", exc_info=True)

    return result


def get_inferred_definition_by_name(name: str) -> ColumnDefinition | None:
    # Get inferred definition by name
    return get_infer_from_standard_name(name) if is_standard_name(name) else get_infer_from_random_name(name)


def is_standard_name(name: str) -> bool:
    # Check the name is standard name
    if ":" not in name:
        return False
    if name.split(":")[0] not in ["concept", "lifecycle", "org", "time", "case"]:
        return False
    return True


def get_infer_from_standard_name(name: str) -> ColumnDefinition | None:
    # Get inferred definition from standard name
    result = None

    try:
        if name == "case:concept:name":
            result = ColumnDefinition.CASE_ID
        elif name == "concept:name":
            result = ColumnDefinition.ACTIVITY
        elif name == "time:timestamp":
            result = ColumnDefinition.TIMESTAMP
        elif name == "lifecycle:transition":
            result = ColumnDefinition.TRANSITION
        elif name == "org:resource":
            result = ColumnDefinition.RESOURCE
    except Exception as e:
        logger.warning(f"Get infer from standard name error: {e}", exc_info=True)

    return result


def get_infer_from_random_name(name: str) -> ColumnDefinition | None:
    # Get inferred definition from random name
    result = None

    try:
        if any(case_id_str == name.lower() for case_id_str in ["case id", "case_id", "caseid"]):
            result = ColumnDefinition.CASE_ID
        elif any(activity_str == name.lower() for activity_str in ["activity", "task", "action"]):
            result = ColumnDefinition.ACTIVITY
        elif "timestamp" in name.lower():
            result = ColumnDefinition.TIMESTAMP
        elif "transition" in name.lower():
            result = ColumnDefinition.TRANSITION
        elif is_resource_column(name):
            result = ColumnDefinition.RESOURCE
        elif is_start_time_column(name):
            result = ColumnDefinition.START_TIMESTAMP
        elif is_end_time_column(name):
            result = ColumnDefinition.END_TIMESTAMP
        elif "duration" in name.lower():
            result = ColumnDefinition.DURATION
        elif "cost" in name.lower():
            result = ColumnDefinition.COST
    except Exception as e:
        logger.warning(f"Get infer from random name error error: {e}", exc_info=True)

    return result


def is_resource_column(name: str) -> bool:
    # Check if the column is resource column
    return any(resource_str == name.lower()
               for resource_str in ["resource", "user", "person", "agent", "employee", "operator", "representative",
                                    "personnel", "specialist", "worker", "staff", "technician", "technologist"])


def is_start_time_column(name: str) -> bool:
    # Check if the column is start time column
    start_time_prefix_list = ["start", "begin"]
    time_suffix_list = ["time", "date", "timestamp"]
    connection_list = ["_", " ", "-", ":", ".", ""]
    return any(f"{start_time_prefix}{connection}{time_suffix}" == name.lower()
               for start_time_prefix in start_time_prefix_list for time_suffix in time_suffix_list
               for connection in connection_list)


def is_end_time_column(name: str) -> bool:
    # Check if the column is end time column
    end_time_prefix_list = ["end", "finish", "complete", "stop"]
    time_suffix_list = ["time", "date", "timestamp"]
    connection_list = ["_", " ", "-", ":", ".", ""]
    return any(f"{end_time_prefix}{connection}{time_suffix}" == name.lower()
               for end_time_prefix in end_time_prefix_list for time_suffix in time_suffix_list
               for connection in connection_list)


def get_activities_count(df: DataFrame, definition: dict[str, ColumnDefinition]) -> dict[str, int]:
    # Get activities count
    result = {}

    try:
        activity_column_name = get_defined_column_name(definition, ColumnDefinition.ACTIVITY)
        transition_column_name = get_defined_column_name(definition, ColumnDefinition.TRANSITION)

        if transition_column_name != "":
            df = df[df[transition_column_name].str.lower() == "complete"]

        result = df[activity_column_name].value_counts().to_dict()
    except Exception as e:
        logger.warning(f"Get activities count error: {e}", exc_info=True)

    return result
