import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from pandas import DataFrame
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

from core.enums.definition import ColumnDefinition
from core.functions.training.util import get_ordinal_encoded_df
from plugins.common.algorithm import Algorithm, get_null_output

# Enable logging
logger = logging.getLogger(__name__)


class KNNAlgorithm(Algorithm):
    def __init__(self, basic_info: Dict[str, Any], project_id: int, plugin_id: Optional[int] = None,
                 df: Optional[DataFrame] = None, model_name: str = None, treatment_definition: list = None):
        super().__init__(basic_info, project_id, plugin_id, df, model_name, treatment_definition)
        self.__grouped_activities = []
        self.__lengths = []

    def preprocess(self) -> bool:
        # Pre-process the data
        try:
            encoded_df, mapping = get_ordinal_encoded_df(self.get_df(), ColumnDefinition.ACTIVITY)
            self.set_data_value("mapping", {v: k for k, v in mapping.items()})
            case_ids = encoded_df[ColumnDefinition.CASE_ID].values
            activities = encoded_df[ColumnDefinition.ACTIVITY].values
            unique_case_ids = np.unique(case_ids)
            self.__grouped_activities = [activities[case_ids == case_id] for case_id in unique_case_ids]
            self.__lengths = [len(case) for case in self.__grouped_activities]
        except Exception as e:
            logger.warning(f"Pre-processing failed: {e}", exc_info=True)
            return False
        return True

    def train(self) -> bool:
        # Train the model
        try:
            min_length = min(self.__lengths)
            max_length = max(self.__lengths)
            threshold = 100  # The minimum number of cases needed to train the model
            models = {}
            scores = {}
            for length in range(min_length, max_length):
                if len([group for group in self.__grouped_activities if len(group) > length]) < threshold:
                    continue
                x = [group[:length] for group in self.__grouped_activities if len(group) > length]
                y = [group[length] for group in self.__grouped_activities if len(group) > length]
                x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)
                knn = KNeighborsClassifier(n_neighbors=self.get_parameter_value("n_neighbors"))
                knn.fit(x_train, y_train)
                models[length] = knn

                # Evaluate the model on the validation set
                y_pred = knn.predict(x_val)
                accuracy = round(knn.score(x_val, y_val), 4)
                precision = round(precision_score(y_val, y_pred, average="weighted", zero_division=1), 4)
                recall = round(recall_score(y_val, y_pred, average="weighted", zero_division=1), 4)
                f1 = round(f1_score(y_val, y_pred, average="weighted"), 4)
                scores[length] = {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1
                }
            self.set_data_value("models", models)
            self.set_data_value("scores", scores)
        except Exception as e:
            logger.warning(f"Training failed: {e}", exc_info=True)
            return False
        return True

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the next activity
        if any(x["ACTIVITY"] not in self.get_data()["mapping"] for x in prefix):
            return get_null_output(self.get_basic_info()["name"], self.get_basic_info()["prescription_type"],
                                   "The prefix contains an activity that is not in the training set")

        # Get the length of the prefix
        length = len(prefix)
        model = self.get_data()["models"].get(length)
        if not model:
            return get_null_output(self.get_basic_info()["name"], self.get_basic_info()["prescription_type"],
                                   "The model is not trained for the given prefix length")

        # Get the features of the prefix
        features = [self.get_data()["mapping"][x["ACTIVITY"]] for x in prefix]

        # Predict the next activity
        prediction = model.predict([features])[0]
        output = list(self.get_data()["mapping"].keys())[list(self.get_data()["mapping"].values()).index(prediction)]
        return {
            "date": datetime.now().isoformat(),
            "type": self.get_basic_info()["prescription_type"],
            "output": output,
            "plugin": {
                "name": self.get_basic_info()["name"],
                "model": length,
                "accuracy": self.get_data()["scores"][length]["accuracy"],
                "precision": self.get_data()["scores"][length]["precision"],
                "recall": self.get_data()["scores"][length]["recall"],
                "f1_score": self.get_data()["scores"][length]["f1_score"]
            }
        }
