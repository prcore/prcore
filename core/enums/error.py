from enum import Enum


class ErrorType(str, Enum):
    EVENT_LOG_BAD_ZIP = "ZIP file is corrupted"
    EVENT_LOG_INVALID = "No valid event log provided"
    EVENT_LOG_NOT_FOUND = "Event log not found"
    EVENT_LOG_DEFINITION_NOT_FOUND = "Event log definition not found"
    EVENT_LOG_COLUMNS_MISMATCH = "Event log columns mismatch with previous definition"

    FAST_MODE_ENFORCED = "Fast mode enforced"

    INVALID_STREAMING_TYPE = "Invalid streaming type"
    INVALID_DATASET_TYPE = "Invalid dataset type"

    PLUGIN_NOT_FOUND = "Plugin not found"
    PLUGIN_NOT_READY = "Plugin not ready"
    PLUGIN_TRIGGER_TYPE_NOT_VALID = "Plugin trigger type not valid"
    PLUGIN_ALREADY_DISABLED = "Plugin already disabled"
    PLUGIN_ALREADY_ENABLED = "Plugin already enabled"

    PROCESS_DATASET_ERROR = "There was an error processing the dataset"

    PROJECT_NOT_FOUND = "Project not found"
    PROJECT_ERROR = "Project is in error status"
    PROJECT_EXISTED = "Project already existed for this event log"
    PROJECT_NOT_READY = "Project not ready"
    PROJECT_NOT_PREPROCESSED = "Project not preprocessed"
    PROJECT_NOT_TRAINED = "Project not trained"
    PROJECT_NOT_STREAMING = "Project not streaming"
    PROJECT_ALREADY_READING = "Project streaming result already be reading"

    RESULT_NOT_FOUND = "Result not found"

    SIMULATION_STARTED = "Simulation already started"
    STREAMING_STARTED = "Streaming already started"
    STREAMING_NOT_STARTED = "Streaming not started"
