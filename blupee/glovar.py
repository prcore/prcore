import logging
from threading import Lock

from plugins.algo_knn import Algorithm as AlgorithmKNN
from plugins.algo_random import Algorithm as AlgorithmRandom

# Enable logging
logger = logging.getLogger(__name__)

identifiers = set(range(1, 10000000))
save_lock = Lock()
algo_classes = [AlgorithmKNN, AlgorithmRandom]

cases: list = []
dashboards: list = []
events: list = []
models: list = []
prescribing_tasks: list = []
results: list = []
training_tasks: list = []
previous_event_logs: list = []
current_event_logs: list = []
