import logging
from datetime import datetime

from pandas import Timestamp
from pydantic import BaseModel

import core.enums.definition

from core.enums.definition import Operator
from core.schemas.definition import ProjectDefinition

# Enable logging
logger = logging.getLogger(__name__)


class CreateProjectRequest(BaseModel):
    event_log_id: int
    positive_outcome: list[list[ProjectDefinition]]
    treatment: list[list[ProjectDefinition]]
