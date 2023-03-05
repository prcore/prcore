from enum import Enum


class ProjectStatus(str, Enum):
    """Enum for project status."""
    WAITING = "WAITING"
    PREPROCESSING = "PREPROCESSING"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    STREAMING = "STREAMING"
    SIMULATING = "SIMULATING"


class PluginStatus(str, Enum):
    """Enum for plugin status."""
    WAITING = "WAITING"
    PREPROCESSING = "PREPROCESSING"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    STREAMING = "STREAMING"


class ProjectStatusGroup(list[ProjectStatus], Enum):
    """Enum for project status group."""
    PROCESSED = [ProjectStatus.TRAINING, ProjectStatus.TRAINED, ProjectStatus.STREAMING, ProjectStatus.SIMULATING]


class PluginStatusGroup(list[PluginStatus], Enum):
    """Enum for plugin status group."""
    WAITING = [PluginStatus.WAITING, PluginStatus.PREPROCESSING, PluginStatus.TRAINING, PluginStatus.TRAINED,
               PluginStatus.STREAMING]
    PREPROCESSING = [PluginStatus.PREPROCESSING, PluginStatus.TRAINING, PluginStatus.TRAINED, PluginStatus.STREAMING]
    TRAINING = [PluginStatus.TRAINING, PluginStatus.TRAINED, PluginStatus.STREAMING]
    TRAINED = [PluginStatus.TRAINED, PluginStatus.STREAMING]
    STREAMING = [PluginStatus.STREAMING]
