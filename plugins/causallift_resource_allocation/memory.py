import logging
from datetime import datetime
from typing import Dict

# Enable logging
logger = logging.getLogger(__name__)

# Data stored in memory
resources: Dict[int, Dict[str, datetime]] = {}
