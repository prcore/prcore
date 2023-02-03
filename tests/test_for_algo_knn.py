from typing import List

from core.models.event import Event
from core.models.training_task import TrainingTask
from plugins.algo_knn import Algorithm as KNNAlgorithm

from load_dataset import get_cases
from load_test_data import get_test_prefix


def init_algorithm() -> KNNAlgorithm:
    # Initialize the algorithm
    cases = get_cases()
    algorithm = KNNAlgorithm(cases)
    return algorithm


def test_prediction(algorithm: KNNAlgorithm, prefix: List[Event]):
    algorithm.predict(prefix)


def main():
    print("Initializing algorithm...")
    algorithm = init_algorithm()
    algorithm.training_task = TrainingTask(id=1, status="testing")
    print("Algorithm initialized.")
    print("Training...")
    algorithm.train()
    print("Predicting...")
    prefix = get_test_prefix()
    test_prediction(algorithm, prefix)
    print("Prediction finished.")


if __name__ == "__main__":
    main()
