import logging
from typing import Any

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class UpdatePluginRequest(BaseModel):
    parameters: dict[str, Any] = {}
    additional_info: dict[str, Any] = {}
