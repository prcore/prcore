import logging
from threading import Lock

from tomli import load

from core.confs.path import CONFIG_PATH
from plugins.algo_knn import Algorithm as AlgorithmKNN
from plugins.algo_random import Algorithm as AlgorithmRandom
from plugins.algo_casual_lift import Algorithm as AlgorithmCasualLift

# Enable logging
logger = logging.getLogger(__name__)

# Load the config
with open(CONFIG_PATH, mode="rb") as fp:
    config = load(fp)
token = config["core"]["security"]["token"]

identifiers = set(range(1, 10000000))
save_lock = Lock()
algo_classes = [AlgorithmKNN, AlgorithmRandom, AlgorithmCasualLift]

cases: list = []
dashboards: list = []
events: list = []
models: list = []
prescribing_tasks: list = []
results: list = []
training_tasks: list = []
previous_event_logs: list = []
current_event_logs: list = []
