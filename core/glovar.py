import logging
import os
from threading import Lock

from pandas import DataFrame
from tomli import load

from core.confs.path import CONFIG_PATH

# Enable logging
logger = logging.getLogger(__name__)

# Load the config
with open(CONFIG_PATH, mode="rb") as fp:
    config = load(fp)
    token = config["core"]["security"]["token"]
    username = config["core"]["security"]["username"]
    password = config["core"]["security"]["password"]

# Load the environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
POSTGRES_DB = os.environ.get('POSTGRES_DB')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

if any(env is None for env in (DB_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)):
    raise ValueError("Missing environment variables")

# Data in memory
dataframes: dict[int, DataFrame] = {}

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
