import math
import pickle
from copy import deepcopy
from typing import Any, List, Union
from time import time

from blupee.confs import path
from blupee.models.case import Case
from blupee.utils.file import get_new_path

from sklearn.ensemble import RandomForestClassifier

from .helper import get_negative_alarm


class Algorithm:
    training_task = Any

    def __init__(self, data):
        self.name = "Casual Lift Algorithm"
        self.description = ("This algorithm uses Uplift Modeling package 'CasualLift' "
                            "to predict the CATE and treatment label.")
        self.data = deepcopy(data)
        self.training_datasets = {}
        self.models = {}
        self.lengths = []
        self.training_data, self.test_data = self.load_training_data()
        self.activity_map = self.pre_process()
        self.parameters = {
            "metric_type": "duration",
            "metric_expectation": "min",
            "min_prefix_length": self.get_min_length(),
            "max_prefix_length": self.get_avg_length(),
            "value_threshold": self.get_value_threshold(self.training_data),
            "proba_threshold": 0.6,
        }
        self.set_training_datasets()
        self.model = None

    def is_applicable(self):  # noqa
        # check if the algorithm can be applied to the data
        return True

    def set_parameters(self, parameters):
        # set the parameters of the algorithm
        if not self.validate_parameters(parameters):
            return False
        self.parameters = parameters

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

    def load_training_data(self) -> (List[Case], List[Case]):
        # split the data into training and test data
        data_length = len(self.data)
        training_data = self.data[:int(data_length * 0.8)]  # noqa
        test_data = self.data[int(data_length * 0.8):]  # noqa
        return training_data, test_data

    def pre_process(self):
        # pre-process the data
        self.calculate_lengths()
        activity_map = self.get_activity_map()
        return activity_map

    def calculate_lengths(self):
        # calculate the lengths of the traces
        for case in self.training_data:
            self.lengths.append(len(case.events))

    def get_activity_map(self):
        # get all possible activities
        activities = set()
        for case in self.training_data:
            for event in case.events:
                activities.add(event.activity)
        activities = list(activities)

        # map activities to numbers
        activity_map = {}
        for i in range(len(activities)):
            activity_map[activities[i]] = i

        return activity_map

    def get_min_length(self):
        # get the minimum length of the traces
        return min(self.lengths) if min(self.lengths) > 3 else 3

    def get_avg_length(self):
        # get the average length of the traces
        return math.floor(sum(self.lengths) / len(self.lengths))

    def get_value_threshold(self, training_data: List[Case]):
        # get the value threshold
        training_data.sort()
        return (self.get_metric_values(training_data)[int(len(training_data) * 0.8)]  # noqa
                if self.parameters["metric_expectation"] == "min"
                else self.get_metric_values(training_data)[int(len(training_data) * 0.2)])  # noqa

    def get_metric_values(self, training_data: List[Case]):
        # get the average metric value of the training data
        values = []
        for case in training_data:
            values.append(self.get_metric_value(case))
        return values

    def get_metric_value(self, case: Case):    # noqa
        # get the selected metric values of the training data
        # for now, we just select duration as the metric
        start_time = case.events[0].start_timestamp
        end_time = case.events[-1].end_timestamp
        return end_time - start_time

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
                if len(case.events) < length:
                    continue
                data_list: List[Union[int, str]] = self.feature_extraction(case.events[:length])
                data_list.append(self.get_label(case))
                training_data.append(data_list)
            print(f"Length {length} training data: {len(training_data)}")

            if len(training_data) < 100:
                continue

            self.training_datasets[length] = training_data

    def feature_extraction(self, prefix):
        # extract features from the prefix
        return [self.activity_map[event.activity] for event in prefix]

    def get_label(self, case):
        value = self.get_metric_value(case)
        if self.parameters["metric_expectation"] == "min":
            return 1 if value <= self.parameters["value_threshold"] else 0
        else:
            return 1 if value > self.parameters["value_threshold"] else 0

    def train(self):
        # train the algorithm on the data
        print(self.name + " is training...")
        # train the model for each length
        for length in self.training_datasets.keys():  # noqa
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

    def predict(self, prefix):
        # predict the negative outcome possibility for a prefix

        # get the length of the prefix
        length = len(prefix)
        print("Random Forest is predicting for length " + str(length))

        # get the model for the length
        model = self.models.get(length, None)  # noqa

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
            "date": int(time()),  # noqa
            "type": "alarm",
            "output": alarm,
            "algorithm": self.name
        }