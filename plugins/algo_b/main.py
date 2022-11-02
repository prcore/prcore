from time import sleep
from typing import Any


class Algorithm:
    parameters = {
        "param1": "value1",
        "param2": "value2",
        "param3": "value3",
    }
    training_task = Any

    def __init__(self, data):
        self.data_path = data
        self.data = self.load_training_data()
        self.name = "Algorithm B"
        self.description = "This is a description of the algorithm"

    def load_training_data(self):
        # load the training data from date_path
        return [f"FakeData{i}" for i in self.data_path]

    def is_applicable(self):  # noqa
        # check if the algorithm can be applied to the data
        return True

    def pre_process(self):
        # do some pre-processing on the data
        pass

    def train(self):
        # train the algorithm on the data
        print(self.name + " is training...")
        sleep(5)
        print(self.name + " has finished training")
        self.training_task.status = "finished"

    def save_model(self):
        # save the model to a file
        pass

    def load_model(self):
        # load the model from a file
        pass

    def predict(self, model, data):
        # predict the output of the data
        pass
