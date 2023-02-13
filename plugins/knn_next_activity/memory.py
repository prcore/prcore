import logging
from datetime import datetime
from typing import Any, Dict

# Enable logging
logger = logging.getLogger(__name__)

# Data stored in memory
instances: Dict[int, Any] = {}
processed_messages: dict[str, datetime] = {}
