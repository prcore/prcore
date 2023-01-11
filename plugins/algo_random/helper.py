from random import random


def get_negative_alarm(predictions, threshold) -> bool:
    # get the negative alarm
    return random() > 0.8
