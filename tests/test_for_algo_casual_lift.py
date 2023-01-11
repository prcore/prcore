from typing import List

from blupee.models.event import Event
from plugins.algo_casual_lift import Algorithm as CasualLiftAlgorithm

from load_dataset import get_cases
from load_test_data import get_test_prefix


def init_algorithm() -> CasualLiftAlgorithm:
    # initialize the algorithm
    cases = get_cases()
    algorithm = CasualLiftAlgorithm(cases)
    return algorithm


def test_prediction(algorithm: CasualLiftAlgorithm, prefix: List[Event]):
    algorithm.predict(prefix)


def main():
    print("Initializing algorithm...")
    algorithm = init_algorithm()
    print("Algorithm initialized.")
    print("Predicting...")
    prefix = get_test_prefix()
    test_prediction(algorithm, prefix)
    print("Prediction finished.")


if __name__ == "__main__":
    main()
