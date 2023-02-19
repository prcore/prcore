import logging
from datetime import datetime
from multiprocessing import Event

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)

# Data in memory
available_plugins: dict[str, dict[str, datetime | str]] = {}
dataframes: dict[int, DataFrame] = {}
processed_messages: dict[str, datetime] = {}
reading_projects: set[int] = set()
simulation_events: dict[int, Event] = {}
simulation_projects: dict[int, datetime] = {}
