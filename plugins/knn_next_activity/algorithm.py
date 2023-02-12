import logging
import pickle
from datetime import datetime

import numpy as np
from pandas import DataFrame
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.general.file import get_new_path
from core.functions.plugin.common import get_null_output
from core.functions.training.util import get_ordinal_encoded_df

from plugins.knn_next_activity.config import basic_info

# Enable logging
logger = logging.getLogger(__name__)


class Algorithm:
    def __init__(self, project_id: int, df: DataFrame, model_name: str = None,
                 parameters: dict = basic_info["parameters"]):
        self.df: DataFrame = df
        self.model_name: str = model_name
        self.parameters: dict = parameters
        self.grouped_activities = []
        self.lengths = []
        self.data = {
            "project_id": project_id,
            "models": {},
            "scores": {},
            "mapping": {}
        }

    def preprocess(self) -> bool:
        # Pre-process the data
        try:
            encoded_df, mapping = get_ordinal_encoded_df(self.df, ColumnDefinition.ACTIVITY)
            self.data["mapping"] = mapping
            case_ids = encoded_df[ColumnDefinition.CASE_ID].values
            activities = encoded_df[ColumnDefinition.ACTIVITY].values
            unique_case_ids = np.unique(case_ids)
            self.grouped_activities = [activities[case_ids == case_id] for case_id in unique_case_ids]
            self.lengths = [len(case) for case in self.grouped_activities]
        except Exception as e:
            logger.warning(f"Pre-processing failed: {e}", exc_info=True)
            return False
        return True

    def train(self) -> bool:
        # Train the model
        try:
            min_length = min(self.lengths)
            max_length = max(self.lengths)
            threshold = 100  # The minimum number of cases needed to train the model
            for length in range(min_length, max_length):
                if len([group for group in self.grouped_activities if len(group) > length]) < threshold:
                    continue
                x = [group[:length] for group in self.grouped_activities if len(group) > length]
                y = [group[length] for group in self.grouped_activities if len(group) > length]
                x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)
                knn = KNeighborsClassifier(n_neighbors=5)
                knn.fit(x_train, y_train)
                self.data["models"][length] = knn

                # Evaluate the model on the validation set
                y_pred = knn.predict(x_val)
                accuracy = knn.score(x_val, y_val)
                precision = precision_score(y_val, y_pred, average='weighted', zero_division=1)
                recall = recall_score(y_val, y_pred, average='weighted', zero_division=1)
                f1 = f1_score(y_val, y_pred, average='weighted')
                self.data["scores"][length] = {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1
                }
        except Exception as e:
            logger.warning(f"Training failed: {e}", exc_info=True)
            return False
        return True

    def save_model(self) -> str:
        # Save the model
        result = ""
        try:
            model_path = get_new_path(f"{path.PLUGIN_MODEL_PATH}/", suffix=".pkl")
            with open(model_path, "wb") as f:
                pickle.dump(self.data, f)
            result = model_path.split("/")[-1]
        except Exception as e:
            logger.warning(f"Saving model failed: {e}", exc_info=True)
        return result

    def load_model(self) -> bool:
        # Load the model
        if self.data["models"]:
            return True
        if not self.model_name:
            return False
        try:
            with open(f"{path.PLUGIN_MODEL_PATH}/{self.model_name}", "rb") as f:
                self.data = pickle.load(f)
        except Exception as e:
            logger.warning(f"Loading model failed: {e}", exc_info=True)
            return False
        return True

    def predict(self, prefix: list[dict]) -> dict:
        # Predict the next activity
        if any(x["ACTIVITY"] not in self.data["mapping"] for x in prefix):
            return get_null_output(basic_info["name"], basic_info["type"],
                                   "The prefix contains an activity that is not in the training set")

        # Get the length of the prefix
        length = len(prefix)
        model = self.data["models"].get(length)
        if not model:
            return get_null_output(basic_info["name"], basic_info["type"],
                                   "The model is not trained for the given prefix length")

        # Get the features of the prefix
        features = [self.data["mapping"][x["ACTIVITY"]] for x in prefix]

        # Predict the next activity
        prediction = model.predict([features])[0]
        output = list(self.data["mapping"].keys())[list(self.data["mapping"].values()).index(prediction)]
        return {
            "date": datetime.now(),
            "type": basic_info["type"],
            "output": output,
            "plugin": {
                "name": basic_info["name"],
                "model": length,
                "accuracy": self.data["scores"][length]["accuracy"],
                "precision": self.data["scores"][length]["precision"],
                "recall": self.data["scores"][length]["recall"],
                "f1_score": self.data["scores"][length]["f1_score"]
            }
        }

    def set_parameters(self, parameters):
        # Set the parameters of the algorithm
        self.parameters = parameters
