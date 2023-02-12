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
    PREPROCESSING = "PREPROCESSING"
    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    ACTIVATING = "ACTIVATING"
    STREAMING = "STREAMING"


class PluginStatusGroup(list[PluginStatus], Enum):
    """Enum for plugin status group."""
    WAITING = [PluginStatus.WAITING, PluginStatus.PREPROCESSING, PluginStatus.TRAINING, PluginStatus.TRAINED,
               PluginStatus.ACTIVATING, PluginStatus.STREAMING]
    PREPROCESSING = [PluginStatus.PREPROCESSING, PluginStatus.TRAINING, PluginStatus.TRAINED, PluginStatus.ACTIVATING,
                     PluginStatus.STREAMING]
    TRAINING = [PluginStatus.TRAINING, PluginStatus.TRAINED, PluginStatus.ACTIVATING, PluginStatus.STREAMING]
    TRAINED = [PluginStatus.TRAINED, PluginStatus.ACTIVATING, PluginStatus.STREAMING]
    ACTIVATING = [PluginStatus.ACTIVATING, PluginStatus.STREAMING]
    STREAMING = [PluginStatus.STREAMING]
