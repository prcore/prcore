import math
from copy import deepcopy
from typing import Any, List, Union
from time import time

from blupee.models.case import Case

from causallift import CausalLift
from pandas import DataFrame


class Algorithm:
    training_task = Any

    def __init__(self, data: List[Case]):
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
            "value_threshold": 0,
            "cate_threshold": 0.6,
        }
        self.set_value_threshold()
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
        return 3 if max(self.lengths) > 3 else min(self.lengths)

    def get_avg_length(self):
        # get the average length of the traces
        return math.floor(sum(self.lengths) / len(self.lengths))

    def set_value_threshold(self):
        # set the value threshold
        print(f"Value threshold: {self.get_value_threshold(self.training_data)}")
        self.parameters["value_threshold"] = self.get_value_threshold(self.training_data)

    def get_value_threshold(self, training_data: List[Case]):
        # get the value threshold
        values = self.get_metric_values(training_data)
        print(f"Values min: {min(values)}")  # noqa
        print(f"Values max: {max(values)}")  # noqa
        return (values[int(len(training_data) * 0.8)] if self.parameters["metric_expectation"] == "min"  # noqa
                else values[int(len(training_data) * 0.2)])  # noqa

    def get_metric_values(self, training_data: List[Case]) -> List[int]:
        # get the average metric value of the training data
        values = []
        for case in training_data:
            values.append(self.get_metric_value(case))
        values.sort()
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
            "length_1": [event1, event2, event3, ..., outcome, treatment],
            "length_2": [event1, event2, event3, ..., outcome, treatment],
            ...
        """
        print(f"Min length: {min(self.lengths)}")
        for length in range(self.parameters["min_prefix_length"], self.parameters["max_prefix_length"] + 1):
            training_data = []
            for case in self.training_data:
                if len(case.events) < length:
                    continue
                data_list: List[Union[int, str]] = self.feature_extraction(case.events[:length])
                data_list.append(self.get_outcome(case))
                data_list.append(self.get_treatment(case))
                training_data.append(data_list)
            print(f"Length {length} training data: {len(training_data)}")

            if len(training_data) < 100:
                continue

            training_df = DataFrame(training_data, columns=self.get_columns(length))  # noqa
            self.training_datasets[length] = training_df

    def feature_extraction(self, prefix):
        # extract features from the prefix
        return [self.activity_map[event.activity] for event in prefix]

    def get_outcome(self, case):
        value = self.get_metric_value(case)
        if self.parameters["metric_expectation"] == "min":
            return 1 if value <= self.parameters["value_threshold"] else 0
        else:
            return 1 if value > self.parameters["value_threshold"] else 0

    def get_treatment(self, case):  # noqa
        if len(case.events) < 1:
            return 0
        return 0 if case.events[0].attributes.get("treatment", 'noTreat') == 'noTreat' else 1

    def get_columns(self, length): # noqa
        # get the columns of the training data
        return [f"event_{i}" for i in range(length)] + ["Outcome", "Treatment"]

    def train(self):
        # train the algorithm on the data
        print(self.name + " is not needed to train in this phase")
        print("Training data is already prepared")
        self.training_task.status = "finished"

    def predict(self, prefix):
        # predict the proba_if_treated, proba_if_untreated, and CATE

        # get the length of the prefix
        length = len(prefix)

        if length < self.parameters["min_prefix_length"] or length > self.parameters["max_prefix_length"]:
            return None

        # check if the activities in prefix are met in the training phase
        if any(x.activity not in self.activity_map for x in prefix):
            return None

        # get the features of the prefix
        features = self.feature_extraction(prefix)

        print("Training model for trace length " + str(length))
        print('The data length of training data: ' + str(len(self.training_datasets[length])))
        train_df = self.training_datasets[length]
        test_df = DataFrame([features], columns=[f"event_{i}" for i in range(length)])  # noqa
        cl = CausalLift(train_df=train_df, test_df=test_df, enable_ipw=True)
        print(self.name + " has finished training for length " + str(length))
        print("CasualLift is predicting for length " + str(length))
        train_df, test_df = cl.estimate_cate_by_2_models()

        # get the prediction of the test_df
        proba_if_treated = test_df["Proba_if_Treated"].values[0].item()
        proba_if_untreated = test_df["Proba_if_Untreated"].values[0].item()
        cate = test_df["CATE"].values[0].item()

        print(test_df.to_string())

        return {
            "date": int(time()),  # noqa
            "type": "cate_prediction",
            "output": {
                "proba_if_treated": proba_if_treated,
                "proba_if_untreated": proba_if_untreated,
                "cate": cate
            },
            "model": {
                "name": self.name
            }
        }
