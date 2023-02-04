from enum import Enum


class ColumnDefinition(str, Enum):
    """Enum for column definitions."""
    CASE_ID = "CASE_ID"
    TRANSITION = "TRANSITION"
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    ACTIVITY = "ACTIVITY"
    TIMESTAMP = "TIMESTAMP"
    RESOURCE = "RESOURCE"
    DURATION = "DURATION"
    COST = "COST"
    START_TIMESTAMP = "START_TIMESTAMP"
    END_TIMESTAMP = "END_TIMESTAMP"
