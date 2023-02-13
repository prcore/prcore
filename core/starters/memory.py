import logging
from datetime import datetime
from multiprocessing import Event

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)

# Data in memory
dataframes: dict[int, DataFrame] = {}
available_plugins: dict[str, dict[str, datetime | str]] = {}
processed_messages: dict[str, datetime] = {}
simulation_events: dict[int, Event] = {}
