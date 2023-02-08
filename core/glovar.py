import logging
from multiprocessing import Process
from threading import Lock

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)

# Data in memory
dataframes: dict[int, DataFrame] = {}
pre_processing_tasks: dict[int, Process] = {}


# Legacy code
identifiers = set(range(1, 10000000))
save_lock = Lock()
algo_classes = []

cases: list = []
dashboards: list = []
events: list = []
models: list = []
prescribing_tasks: list = []
results: list = []
training_tasks: list = []
previous_event_logs: list = []
current_event_logs: list = []
