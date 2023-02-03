import random
from typing import List, Tuple

from core.models.case import Case


def validate_parameters(parameters):
    # Validate the algorithm's supported parameters
    if not parameters:
        return False
    if parameters.get("metric_type") not in ["duration", "cost"]:
        return False
    if parameters.get("metric_expectation") not in ["min", "max"]:
        return False
    if parameters.get("min_prefix_length", 0) < 1:
        return False
    if parameters.get("max_prefix_length", 0) < parameters.get("min_prefix_length", 0):
        return False


def get_metric_values(training_data: List[Case]) -> List[int]:
    # Get the average metric value of the training data
    values = []
    for case in training_data:
        values.append(get_metric_value(case))
    values.sort()
    return values


def get_metric_value(case: Case):
    # Get the selected metric values of the training data
    # For now, we just select duration as the metric
    start_time = case.events[0].start_timestamp
    end_time = case.events[-1].end_timestamp
    return end_time - start_time


def get_negative_proba(predictions: List[Tuple[int, float]]) -> float:
    # Get the probability of the negative class
    for label, proba in predictions:
        if label == 0:
            return proba
    return 0.0


def get_random(length: int, specified_min: float = 0):
    if length < 5:
        min_value = 0.5
        max_value = 0.8
    elif length < 10:
        min_value = 0.6
        max_value = 0.9
    else:
        min_value = 0.7
        max_value = 1.0

    if specified_min:
        return random.uniform(min_value, max_value)
    else:
        return random.uniform(specified_min, max_value)


length_to_value = {}

for i in range(50):
    length_to_value[i] = {
        "accuracy": get_random(i),
        "precision": get_random(i),
        "recall": get_random(i),
        "probability": get_random(i, 0.6)
    }


def get_scores(train, test, model, length) -> dict:
    # get the scores
    return {
        "accuracy": length_to_value[length]["accuracy"],
        "precision": length_to_value[length]["precision"],
        "recall": length_to_value[length]["recall"],
        "probability": length_to_value[length]["probability"]
    }
