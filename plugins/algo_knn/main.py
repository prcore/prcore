from typing import Any
from time import time
from copy import deepcopy

from sklearn.neighbors import KNeighborsClassifier


class Algorithm:
    training_task = Any

    def __init__(self, data):
        self.name = "KNN next activity prediction"
        self.description = "This algorithm predicts the next activity based on the KNN algorithm"
        self.data = deepcopy(data)
        self.training_data, self.test_data = self.load_training_data()
        self.activity_map, self.training_data = self.pre_process()
        self.parameters = {
           "n_neighbors": 3
        }
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

    def pre_process(self):
        # do some pre-processing on the data
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
        # remove the traces that are too short
        self.training_data = [case for case in self.training_data if len(case.events) > 2]  # noqa
        # get every two events and the next event
        training_data = []
        for case in self.training_data:
            for i in range(len(case.events) - 2):  # noqa
                training_data.append(
                    [case.events[i].activity,  # noqa
                     case.events[i + 1].activity,  # noqa
                     case.events[i + 2].activity]  # noqa
                )
        print(len(training_data))
        print(activity_map)
        # map the activities to numbers in training data
        for i in range(len(training_data)):
            training_data[i][0] = activity_map[training_data[i][0]]
            training_data[i][1] = activity_map[training_data[i][1]]
            training_data[i][2] = activity_map[training_data[i][2]]

        return activity_map, training_data

    def train(self):
        # train the algorithm on the data
        print(self.name + " is training...")
        # get training data
        x_train = []
        y_train = []
        for data in self.training_data:
            x_train.append(data[:2])
            y_train.append(data[2])
        # train the model
        model = KNeighborsClassifier(n_neighbors=self.parameters["n_neighbors"])
        model.fit(x_train, y_train)
        print(self.name + " has finished training")
        self.training_task.status = "finished"
        self.model = model

    def save_model(self):
        # save the model
        pass

    def load_model(self):
        # load the model from a file
        pass

    def predict(self, events):
        # predict the output of the data
        # Check if the events are long enough
        print("Knn check condition 1")
        if len(events) < 2:
            return None

        # get the last two events
        x_test = [events[-2].activity, events[-1].activity]

        print("Knn check condition 2")
        print(x_test[0])
        print(x_test[1])
        print(self.activity_map)

        # Check if the events are in the activity map
        if x_test[0] not in self.activity_map or x_test[1] not in self.activity_map:
            return None

        print("Knn start prediction")

        # map the activities to numbers
        x_test[0] = self.activity_map[x_test[0]]
        x_test[1] = self.activity_map[x_test[1]]

        # predict the next activity
        y_pred = self.model.predict([x_test])

        the_prediction = y_pred[0]
        print("Knn prediction: " + str(the_prediction))

        # map the number to an activity
        activity = list(self.activity_map.keys())[list(self.activity_map.values()).index(y_pred[0])]

        if not activity:
            return None

        return {
            "date": int(time()),
            "type": "next_activity",
            "output": activity,
            "algorithm": self.name
        }
