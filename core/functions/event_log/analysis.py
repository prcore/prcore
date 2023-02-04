import logging

from pandas import DataFrame

from core.enums.definition import ColumnDefinition

# Enable logging
logger = logging.getLogger(__name__)


def get_brief_with_inferred_definition(df: DataFrame) -> list[list[str | int | float | bool | ColumnDefinition | None]]:
    # Get brief with inferred definition
    result = []

    try:
        result: list = df.head(5).values.tolist()
        headers = df.columns.tolist()
        inferred_dict = get_inferred_definitions(headers)
        result[0] = [inferred_dict[k]["name"] for k in headers]
        result.insert(1, [inferred_dict[k]["definition"] for k in headers])
    except Exception as e:
        logger.warning(f"Get brief with inferred definition error: {e}", exc_info=True)

    return result


def get_inferred_definitions(headers: list[str]) -> dict[dict[str, ColumnDefinition | None]]:
    # Get inferred definition
    result = []

    try:
        result = {k: get_inferred_definition_by_name(k) for k in headers}
    except Exception as e:
        logger.warning(f"Get inferred definition error: {e}", exc_info=True)

    return result


def get_inferred_definition_by_name(name: str) -> dict[str, ColumnDefinition | None]:
    # Get inferred definition by name
    return get_infer_from_standard_name(name) if is_standard_name(name) else get_infer_from_random_name(name)


def is_standard_name(name: str) -> bool:
    # Check the name is standard name
    if ":" not in name:
        return False
    if name.split(":")[0] not in ["concept", "lifecycle", "org", "time", "case"]:
        return False
    return True


def get_infer_from_standard_name(name: str) -> dict[str, ColumnDefinition | None]:
    # Get inferred definition from standard name
    result = {
        "name": name,
        "definition": None
    }

    try:
        if name == "case:concept:name":
            result["name"] = "Case ID"
            result["definition"] = ColumnDefinition.CASE_ID
        elif name == "concept:name":
            result["name"] = "Activity"
            result["definition"] = ColumnDefinition.ACTIVITY
        elif name == "time:timestamp":
            result["name"] = "Timestamp"
            result["definition"] = ColumnDefinition.TIMESTAMP
        elif name == "lifecycle:transition":
            result["name"] = "Transition"
            result["definition"] = ColumnDefinition.TRANSITION
        elif name == "org:resource":
            result["name"] = "Resource"
            result["definition"] = ColumnDefinition.RESOURCE
    except Exception as e:
        logger.warning(f"Get infer from standard name error: {e}", exc_info=True)

    return result


def get_infer_from_random_name(name: str) -> dict[str, ColumnDefinition | None]:
    # Get inferred definition from random name
    result = {
        "name": name,
        "definition": None
    }

    try:
        if "case" in name.lower():
            result["name"] = "Case ID"
            result["definition"] = ColumnDefinition.CASE_ID
        elif "activity" in name.lower():
            result["name"] = "Activity"
            result["definition"] = ColumnDefinition.ACTIVITY
        elif "timestamp" in name.lower():
            result["name"] = "Timestamp"
            result["definition"] = ColumnDefinition.TIMESTAMP
        elif "transition" in name.lower():
            result["name"] = "Transition"
            result["definition"] = ColumnDefinition.TRANSITION
        elif "resource" in name.lower():
            result["name"] = "Resource"
            result["definition"] = ColumnDefinition.RESOURCE
        elif "start" in name.lower() and "time" in name.lower():
            result["name"] = "Start Timestamp"
            result["definition"] = ColumnDefinition.START_TIMESTAMP
        elif "end" in name.lower() and "time" in name.lower():
            result["name"] = "End Timestamp"
            result["definition"] = ColumnDefinition.END_TIMESTAMP
        elif "duration" in name.lower():
            result["name"] = "Duration"
            result["definition"] = ColumnDefinition.DURATION
        elif "cost" in name.lower():
            result["name"] = "Cost"
            result["definition"] = ColumnDefinition.COST
    except Exception as e:
        logger.warning(f"Get infer from random name error error: {e}", exc_info=True)

    return result
