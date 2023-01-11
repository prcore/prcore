import random


def get_random(length):
    if length < 5:
        min_value = 0.5
        max_value = 0.8
    elif length < 10:
        min_value = 0.6
        max_value = 0.9
    else:
        min_value = 0.7
        max_value = 1.0

    return random.uniform(min_value, max_value)


length_to_value = {}

for i in range(50):
    length_to_value[i] = {
        "accuracy": get_random(i),
        "precision": get_random(i),
        "recall": get_random(i),
        "roc_auc": get_random(i)
    }


def get_scores(train_df, test_df, cl, length) -> dict:
    # get the scores, mock with random, with average performance
    return {
        "accuracy": length_to_value[length]["accuracy"],
        "precision": length_to_value[length]["precision"],
        "recall": length_to_value[length]["recall"],
        "roc_auc": length_to_value[length]["roc_auc"]
    }
