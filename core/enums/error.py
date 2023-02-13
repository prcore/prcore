from enum import Enum


class ErrorType(str, Enum):
    PROJECT_NOT_FOUND = "Project not found"
    PROJECT_ACTIVATING = "Project is activating"
    PROJECT_NOT_TRAINED = "Project not trained"
    PROJECT_NOT_STREAMING = "Project not streaming"
    PROJECT_ALREADY_READING = "Project streaming result already be reading"
    SIMULATION_STARTED = "Simulation already started"
    SIMULATION_NOT_STARTED = "Simulation not started"
