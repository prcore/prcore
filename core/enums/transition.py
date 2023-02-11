from enum import Enum


class Transition(str, Enum):
    """Enum for transition."""
    ASSIGN = "ASSIGN"
    ATE_ABORT = "ATE_ABORT"
    AUTOSKIP = "AUTOSKIP"
    COMPLETE = "COMPLETE"
    MANUALSKIP = "MANUALSKIP"
    PI_ABORT = "PI_ABORT"
    REASSIGN = "REASSIGN"
    RESUME = "RESUME"
    SCHEDULE = "SCHEDULE"
    START = "START"
    SUSPEND = "SUSPEND"
    UNKNOWN = "UNKNOWN"
    WITHDRAW = "WITHDRAW"
