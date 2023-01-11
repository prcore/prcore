from random import choice, random

def get_negative_alarm(predictions, threshold) -> bool:
    # get the negative alarm
    return random() > threshold
