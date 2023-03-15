import logging
from typing import Any

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class UpdateAdditionalInfoRequest(BaseModel):
    additional_info: dict[str, dict[str, Any]] = {}
