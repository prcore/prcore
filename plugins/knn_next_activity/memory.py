import logging
from typing import Any, Dict

# Enable logging
logger = logging.getLogger(__name__)

# Data stored in memory
instances: Dict[int, Any] = {}
