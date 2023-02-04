import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class Definition(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    columns_definition: dict
    outcome_definition: list
    treatment_definition: list
