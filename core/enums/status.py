from enum import Enum


class ProjectStatus(str, Enum):
    """Enum for project status."""
    WAITING = "WAITING"
    PREPROCESSING = "PREPROCESSING"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    ACTIVATING = "ACTIVATING"
    STREAMING = "STREAMING"
    SIMULATING = "SIMULATING"


class PluginStatus(str, Enum):
    """Enum for plugin status."""
    WAITING = "WAITING"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    ACTIVATING = "ACTIVATING"
    STREAMING = "STREAMING"

