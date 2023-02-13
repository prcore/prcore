from enum import Enum


class ErrorType(str, Enum):
    PROJECT_NOT_FOUND = "Project not found"
    PROJECT_ACTIVATING = "Project is activating"
    PROJECT_NOT_TRAINED = "Project not trained"
    PROJECT_NOT_STREAMING = "Project not streaming"
    SIMULATION_STARTED = "Simulation already started"
    SIMULATION_NOT_STARTED = "Simulation not started"
