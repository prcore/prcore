from time import sleep


class Algorithm:
    parameters = {
        "param1": "value1",
        "param2": "value2",
        "param3": "value3",
    }

    def __init__(self, data_path):
        self.data_path = data_path
        self.data = self.load_training_data()
        self.name = "Algorithm B"
        self.description = "This is a description of the algorithm"

    def load_training_data(self):
        # load the training data from date_path
        return [self.data_path]

    def is_applicable(self):  # noqa
        # check if the algorithm can be applied to the data
        return True

    def pre_process(self):
        # do some pre-processing on the data
        pass

    def train(self):
        # train the algorithm on the data
        pass

    def save_model(self):
        # save the model to a file
        pass

    def load_model(self):
        # load the model from a file
        pass

    def predict(self, model, data):
        # predict the output of the data
        pass
