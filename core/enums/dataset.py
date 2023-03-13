from enum import Enum


class EncodingType(str, Enum):
    """Enum for encoding type."""
    BOOLEAN = "BOOLEAN"
    FREQUENCY_BASED = "FREQUENCY_BASED"
    SIMPLE_INDEX = "SIMPLE_INDEX"


class OutcomeType(str, Enum):
    """Enum for outcome type."""
    LABELLED = "LABELLED"
    LAST_ACTIVITY = "LAST_ACTIVITY"
