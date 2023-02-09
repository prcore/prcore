from enum import Enum


class ProjectStatus(str, Enum):
    """Enum for project status."""
    WAITING = "WAITING"
    PREPROCESSING = "PREPROCESSING"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    STREAMING = "STREAMING"


class PluginStatus(str, Enum):
    """Enum for plugin status."""
    WAITING = "WAITING"
    RUNNING = "TRAINING"
    FINISHED = "TRAINED"
    FAILED = "STREAMING"
