import logging
from datetime import datetime
from multiprocessing import Event
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
reading_projects: set[int] = set()
simulation_events: dict[int, Event] = {}
simulation_start_times: dict[int, datetime] = {}
