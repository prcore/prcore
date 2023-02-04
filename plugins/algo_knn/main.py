import math
import pickle
from typing import List, Union
from time import time
from copy import deepcopy

from core.confs import path
from core.models.case import Case
from core.models.training_task import TrainingTask
from core.functions.general import get_new_path

from sklearn.neighbors import KNeighborsClassifier

from .helper import get_scores


class Algorithm:
    training_task: TrainingTask

    def __init__(self, data):
        self.name = "KNN next activity prediction"
        self.description = "This algorithm predicts the next activity based on the KNN algorithm"
        self.data = deepcopy(data)
        self.training_datasets = {}
        self.models = {}
        self.lengths = []
        self.training_data, self.test_data = self.split_data()
        self.activity_map = self.pre_process()
        self.parameters = {
            "n_neighbors": 3,
            "min_prefix_length": self.get_min_length(),
            "max_prefix_length": self.get_avg_length()
        }
        self.set_training_datasets()
        self.model = None

    def is_applicable(self):
        # Check if the algorithm can be applied to the data
        first_case = self.training_data[0]
        first_event = first_case.events[0]
        return bool(first_event.activity)

    def set_parameters(self, parameters):
        # Set the parameters of the algorithm
        self.parameters = parameters

    def split_data(self) -> (List[Case], List[Case]):
        # split the data into training and test data
        data_length = len(self.data)
        training_data = self.data[:int(data_length * 0.8)]  # noqa
        test_data = self.data[int(data_length * 0.8):]  # noqa
        return training_data, test_data

    def pre_process(self):
        # Pre-process the data
        self.calculate_lengths()
        activity_map = self.get_activity_map()
        return activity_map

    def calculate_lengths(self):
        # Calculate the lengths of the traces
        self.lengths = [len(case.events) for case in self.training_data]

    def get_activity_map(self):
        # Get all possible activities
        activities = set()
        for case in self.training_data:
            for event in case.events:
                activities.add(event.activity)
        activities = list(activities)

        # Map activities to numbers (Ordinal Encoding)
        activity_map = {}
        for i in range(len(activities)):
            activity_map[activities[i]] = i

        return activity_map

    def get_min_length(self):
        # Get the minimum length of the traces
        return 3 if max(self.lengths) > 3 else min(self.lengths)

    def get_avg_length(self):
        # Get the average length of the traces
        return math.floor(sum(self.lengths) / len(self.lengths))

    def set_training_datasets(self):
        # Get the training datasets for each length
        """
        :return: {
            "length_1": [event1, event2, event3, ..., outcome_event],
            "length_2": [event1, event2, event3, ..., outcome_event],
            ...
        """
        for length in range(self.parameters["min_prefix_length"], self.parameters["max_prefix_length"] + 1):
            training_data = []
            for case in self.training_data:
                if len(case.events) < length:
                    continue
                data_list: List[Union[int, str]] = self.feature_extraction(case.events[:length])
                training_data.append(data_list)
            print(f"Length {length} training data: {len(training_data)}")

            if len(training_data) < 100:
                continue

            self.training_datasets[length] = training_data

    def feature_extraction(self, prefix):
        # Extract features from the prefix
        return [self.activity_map[event.activity] for event in prefix]

    def train(self):
        # Train the algorithm on the data
        print(self.name + " is training...")
        # Train the model for each length
        for length in self.training_datasets.keys():  # noqa
            self.train_model_for_length(length)
        self.save_model()

    def train_model_for_length(self, length):
        # Train the model for a specific length
        print("Training model for length " + str(length))
        x_train = []
        y_train = []

        for data in self.training_datasets[length]:
            x_train.append(data[:-1])
            y_train.append(data[-1])

        # Train the model
        model = KNeighborsClassifier(n_neighbors=self.parameters["n_neighbors"])
        model.fit(x_train, y_train)
        print(self.name + " has finished training for length " + str(length))
        self.models[length] = model

    def save_model(self):
        # save the model
        model_path = get_new_path(f"{path.MODEL_PATH}/", f"{self.name} - ", ".pkl")
        with open(model_path, "wb") as f:
            pickle.dump(self.models, f)
        self.model = model_path
        self.training_task.status = "finished"

    def load_model(self):
        # load the model from a file
        with open(self.model, "rb") as f:
            self.models = pickle.load(f)

    def predict(self, prefix):
        # Predict the next activity

        # Get the length of the prefix
        length = len(prefix)

        if length < self.parameters["min_prefix_length"] - 1 or length > self.parameters["max_prefix_length"] - 1:
            print("Length is not in the configuration range")
            return None

        print(f"{self.name} is predicting for prefix length: {length}")

        # Get the model for the length
        model = self.models.get(length + 1)  # noqa

        if not model:
            print(self.models.keys())
            print("Model not found for the provided prefix length")
            return None

        # Check if the activities in prefix are met in the training phase
        if any(x.activity not in self.activity_map for x in prefix):
            print("Activity not found for the provided prefix")
            return None

        # Get the features of the prefix
        features = self.feature_extraction(prefix)

        # Predict the next activity
        prediction = model.predict([features])[0]
        activity = list(self.activity_map.keys())[list(self.activity_map.values()).index(prediction)]
        print(f"{self.name} predicted: {activity}")
        scores = get_scores(self.training_data, self.test_data, self.model)

        return {
            "date": int(time()),  # noqa
            "type": "next_activity",
            "output": activity,
            "model": {
                "name": self.name,
                "accuracy": scores["accuracy"],
                "recall": scores["recall"],
                "probability": scores["probability"]
            }
        }
