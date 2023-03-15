from enum import Enum


class PluginType(str, Enum):
    """Enum for plugin type."""
    NEXT_ACTIVITY = "NEXT_ACTIVITY"
    ALARM = "ALARM"
    TREATMENT_EFFECT = "TREATMENT_EFFECT"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
