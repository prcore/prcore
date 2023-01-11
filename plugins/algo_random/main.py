import math
import pickle
from copy import deepcopy
from typing import Any, Union
from time import time

from blupee.confs import path
from blupee.utils.file import get_new_path

from sklearn.ensemble import RandomForestClassifier

from .helper import get_negative_alarm


class Algorithm:
    training_task = Any

    def __init__(self, data):
        self.name = "Random Forest Alarm"
        self.description = "This algorithm prescribes alarms based on the possibility of a case being completed in time."
        self.data = deepcopy(data)
        self.training_datasets = {}
        self.models = {}
        self.lengths = []
        self.training_data, self.test_data = self.load_training_data()
        self.activity_map = self.pre_process()
        self.parameters = {
            "metric_type": "duration",
            "metric_expectation": "min",
            "min_prefix_length": 3,
            "max_prefix_length": self.get_avg_length(),
            "value_threshold": 0,
            "proba_threshold": 0.5,
        }
        self.set_training_datasets()
        self.model = None

    def load_training_data(self):
        # split the data into training and test data
        data_length = len(self.data)
        training_data = self.data[:int(data_length * 0.8)]
        test_data = self.data[int(data_length * 0.8):]
        return training_data, test_data

    def is_applicable(self):  # noqa
        # check if the algorithm can be applied to the data
        return True

    def validate_parameters(self, parameters):    # noqa
        # validate the parameters
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

    def set_parameters(self, parameters):
        # set the parameters of the algorithm
        if not self.validate_parameters(parameters):
            return False
        self.parameters = parameters

    def get_activity_map(self):
        # get all possible activities
        activities = set()
        for case in self.training_data:
            for event in case.events:  # noqa
                activities.add(event.activity)
        activities = list(activities)

        # map activities to numbers
        activity_map = {}
        for i in range(len(activities)):
            activity_map[activities[i]] = i

        return activity_map

    def get_metric_value(self, case):    # noqa
        # get the selected metric values of the training data
        # for now, we just select duration as the metric
        start_time = case.events[0].start_timestamp    # noqa
        end_time = case.events[-1].end_timestamp    # noqa
        return end_time - start_time

    def get_label(self, case):
        value = self.get_metric_value(case)
        if self.parameters["metric_expectation"] == "min":
            return "positive" if value <= self.parameters["value_threshold"] else "negative"
        else:
            return "positive" if value > self.parameters["value_threshold"] else "negative"

    def calculate_lengths(self):
        # calculate the lengths of the traces
        for case in self.training_data:
            self.lengths.append(len(case.events))    # noqa

    def get_max_length(self):
        # get the maximum length of the traces
        return max(self.lengths)

    def get_min_length(self):
        # get the minimum length of the traces
        return min(self.lengths) or 3

    def get_avg_length(self):
        # get the average length of the traces
        return math.floor(sum(self.lengths) / len(self.lengths))

    def set_training_datasets(self):
        # get the training datasets
        """
        :return: {
            "length_1": [event1, event2, event3, ..., label],
            "length_2": [event1, event2, event3, ..., label],
            ...
        """
        for length in range(self.parameters["min_prefix_length"], self.parameters["max_prefix_length"] + 1):
            training_data = []
            for case in self.training_data:
                if len(case.events) < length:    # noqa
                    continue
                data_list: list[Union[int, str]] = self.feature_extraction(case.events[:length])    # noqa
                data_list.append(self.get_label(case))
                training_data.append(data_list)
            print(f"Length {length} training data: {len(training_data)}")

            if len(training_data) < 100:
                continue

            self.training_datasets[length] = training_data

    def feature_extraction(self, prefix):    # noqa
        # extract features from the prefix
        return [self.activity_map[event.activity] for event in prefix]

    def pre_process(self):
        # pre-process the data
        self.calculate_lengths()
        activity_map = self.get_activity_map()

        return activity_map

    def train(self):
        # train the algorithm on the data
        print(self.name + " is training...")
        # train the model for each length
        for length in self.training_datasets.keys():
            self.train_model_for_length(length)
        self.save_model()

    def train_model_for_length(self, length):
        # train the model for a specific length
        x_train = []
        y_train = []

        print("Training model for length " + str(length))
        print('Training data is None: ' + str(self.training_datasets[length] is None))
        print(self.training_datasets[length])

        for data in self.training_datasets[length]:
            x_train.append(data[:-1])
            y_train.append(data[-1])
        # train the model
        model = RandomForestClassifier()
        model.fit(x_train, y_train)
        print(self.name + " has finished training for length " + str(length))
        self.models[length] = model
        self.training_task.status = "finished"

    def save_model(self):
        # save the model
        model_path = get_new_path(f"{path.MODEL_PATH}/", self.name, "pkl")
        with open(model_path, "wb") as f:
            pickle.dump(self.models, f)
        self.model = model_path

    def load_model(self):
        # load the model from a file
        with open(self.model, "rb") as f:
            self.models = pickle.load(f)

    def get_transition_dict(self):    # noqa
        # get the transition system
        """
        :return: {
            "activity_1": ["activity_2", "activity_3", ...],
            "activity_2": ["activity_6", "activity_7", ...],
            ...
            }
        """
        transition_dict = {}
        return transition_dict

    def get_best_activity_based_on_metric(self, kpis):
        # get the best activity based on the metric
        if self.parameters["metric_expectation"] == "min":
            return min(kpis, key=lambda x: x[1])
        else:
            return max(kpis, key=lambda x: x[1])

    def predict(self, prefix):
        # predict the negative outcome possibility for a prefix

        # get the length of the prefix
        length = len(prefix)
        print("Random Forest is predicting for length " + str(length))

        # get the model for the length
        model = self.models.get(length, None)

        if not model:
            return None

        # check if the activities in prefix are met in the training phase
        if any(x.activity not in self.activity_map for x in prefix):
            return None

        # get the features of the prefix
        features = self.feature_extraction(prefix)

        # get the prediction
        predictions = zip(model.classes_, model.predict_proba([features]))

        print("Predictions: ", predictions)
        alarm = get_negative_alarm(predictions, self.parameters["proba_threshold"])

        if not alarm:
            return None

        return {
            "date": int(time()),
            "type": "alarm",
            "output": alarm,
            "algorithm": self.name
        }
