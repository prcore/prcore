import logging
from datetime import datetime
from multiprocessing.synchronize import Event as ProcessEventType
from typing import Any, BinaryIO

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)

# Data in memory
available_plugins: dict[str, dict[str, datetime | str]] = {}
dataframes: dict[int, DataFrame] = {}
log_tests: dict[int, dict[str, datetime | BinaryIO | str]] = {}
ongoing_results: dict[str, Any] = {}
processed_messages: dict[str, datetime] = {}
streaming_projects: dict[int, dict[str, str | bool | datetime | ProcessEventType | None]] = {}
