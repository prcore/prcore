from enum import Enum


class ColumnDefinition(str, Enum):
    """Enum for column definitions."""
    CASE_ID = "CASE_ID"
    TRANSITION = "TRANSITION"
    OUTCOME = "OUTCOME"
    TREATMENT = "TREATMENT"
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
    COMPLETE_INDICATOR = "COMPLETE_INDICATOR"


class DefinitionType(str, Enum):
    """Enum for definition type."""
    TEXT = {ColumnDefinition.TEXT, ColumnDefinition.ACTIVITY, ColumnDefinition.RESOURCE}
    NUMBER = {ColumnDefinition.NUMBER, ColumnDefinition.DURATION, ColumnDefinition.COST}
    BOOLEAN = {ColumnDefinition.BOOLEAN}
    DATETIME = {ColumnDefinition.DATETIME, ColumnDefinition.TIMESTAMP,
                ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP}


class Operator(str, Enum):
    """Enum for outcome operators."""
    # Basic
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    # TEXT
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    # NUMBER
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    # BOOLEAN
    IS_TRUE = "IS_TRUE"
    IS_FALSE = "IS_FALSE"
    # DATETIME
    EARLIER_THAN = "EARLIER_THAN"
    EARLIER_THAN_OR_EQUAL = "EARLIER_THAN_OR_EQUAL"
    LATER_THAN = "LATER_THAN"
    LATER_THAN_OR_EQUAL = "LATER_THAN_OR_EQUAL"


class SupportedOperators(str, Enum):
    """Enum for outcome and treatment supported operators."""
    # TEXT
    TEXT = {Operator.EQUAL, Operator.NOT_EQUAL, Operator.CONTAINS, Operator.NOT_CONTAINS}
    # NUMBER
    NUMBER = {Operator.EQUAL, Operator.NOT_EQUAL, Operator.LESS_THAN, Operator.LESS_THAN_OR_EQUAL,
              Operator.GREATER_THAN, Operator.GREATER_THAN_OR_EQUAL}
    # BOOLEAN
    BOOLEAN = {Operator.EQUAL, Operator.NOT_EQUAL, Operator.IS_TRUE, Operator.IS_FALSE}
    # DATETIME
    DATETIME = {Operator.EQUAL, Operator.NOT_EQUAL, Operator.EARLIER_THAN, Operator.EARLIER_THAN_OR_EQUAL,
                Operator.LATER_THAN, Operator.LATER_THAN_OR_EQUAL}


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
