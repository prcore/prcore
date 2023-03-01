from enum import Enum


class ErrorType(str, Enum):
    DATASET_ERROR = "Dataset error"

    EVENT_LOG_INVALID = "No valid event log provided"
    EVENT_LOG_NOT_FOUND = "Event log not found"
    EVENT_LOG_DEFINITION_NOT_FOUND = "Event log definition not found"

    PROJECT_NOT_FOUND = "Project not found"
    PROJECT_EXISTED = "Project already existed for this event log"
    PROJECT_ACTIVATING = "Project is activating"
    PROJECT_NOT_READY = "Project not ready"
    PROJECT_NOT_TRAINED = "Project not trained"
    PROJECT_NOT_STREAMING = "Project not streaming"
    PROJECT_ALREADY_READING = "Project streaming result already be reading"

    SIMULATION_STARTED = "Simulation already started"
    SIMULATION_NOT_STARTED = "Simulation not started"
