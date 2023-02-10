from enum import Enum


class MessageType(str, Enum):
    """Enum for message type."""
    ONLINE_REPORT = "ONLINE_REPORT"
    ONLINE_INQUIRY = "ONLINE_INQUIRY"
