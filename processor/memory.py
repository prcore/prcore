import logging
from datetime import datetime

# Enable logging
logger = logging.getLogger(__name__)

# Data stored in memory
processed_messages: dict[str, datetime] = {}
pending_dfs: dict[str, dict[str, datetime | str | float]] = {}
