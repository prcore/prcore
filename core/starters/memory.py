import logging
from datetime import datetime
from multiprocessing import Process

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)

# Data in memory
dataframes: dict[int, DataFrame] = {}
pre_processing_tasks: dict[int, Process] = {}
available_plugins: dict[str, dict[str, datetime | str]] = {}
