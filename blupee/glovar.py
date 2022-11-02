import logging
from threading import Lock

from plugins.algo_a import Algorithm as AlgorithmA
from plugins.algo_b import Algorithm as AlgorithmB
from plugins.algo_knn import Algorithm as AlgorithmKNN

# Enable logging
logger = logging.getLogger(__name__)

identifiers = set(range(1, 10000000))
save_lock = Lock()
algo_classes = [AlgorithmA, AlgorithmB, AlgorithmKNN]

cases: list = []
dashboards: list = []
events: list = []
models: list = []
prescribing_tasks: list = []
results: list = []
training_tasks: list = []
previous_event_logs: list = []
current_event_logs: list = []
