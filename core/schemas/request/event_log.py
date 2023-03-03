import logging

from pydantic import BaseModel

from core.enums.definition import ColumnDefinition, Transition

# Enable logging
logger = logging.getLogger(__name__)


class ColumnsDefinitionRequest(BaseModel):
    columns_definition: dict[str, ColumnDefinition | None]
    case_attributes: list[str] | None = None
    fast_mode: bool = True
    start_transition: str = Transition.START
    complete_transition: str = Transition.COMPLETE
    abort_transition: str = Transition.ATE_ABORT
