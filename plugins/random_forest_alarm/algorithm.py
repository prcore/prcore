import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pandas import DataFrame
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from core.enums.definition import ColumnDefinition
from core.functions.training.util import get_ordinal_encoded_df
from plugins.common.algorithm import (Algorithm, get_model_and_features_by_activities, get_prescription_output,
                                      get_encoded_df_from_df_by_activity, get_score, get_null_output)

# Enable logging
logger = logging.getLogger(__name__)


def get_negative_proba(predictions: List[Tuple[int, float]]) -> float:
    # Get the probability of the negative class
    for label, proba in predictions:
        if label == 0:
            return proba
    return 0.0


class RandomAlgorithm(Algorithm):
    def __init__(self, basic_info: Dict[str, Any], project_id: int, plugin_id: Optional[int] = None,
                 df: Optional[DataFrame] = None, model_name: str = None, treatment_definition: list = None):
        super().__init__(basic_info, project_id, plugin_id, df, model_name, treatment_definition)
        self.__grouped_activities = []
        self.__grouped_outcomes = []
        self.__lengths = []
        self.__count_encoding_df = None

    def preprocess(self) -> str:
        # Pre-process the data
        encoded_df, mapping = get_ordinal_encoded_df(self.get_df(), ColumnDefinition.ACTIVITY)
        self.set_data_value("mapping", {v: k for k, v in mapping.items()})
        self.set_data_value("activities_code", list(mapping.keys()))
        case_ids = encoded_df[ColumnDefinition.CASE_ID].values
        activities = encoded_df[ColumnDefinition.ACTIVITY].values
        outcomes = encoded_df[ColumnDefinition.OUTCOME].values
        unique_case_ids = np.unique(case_ids)
        self.__grouped_activities = [activities[case_ids == case_id] for case_id in unique_case_ids]
        self.__grouped_outcomes = [outcomes[case_ids == case_id] for case_id in unique_case_ids]
        self.__lengths = [len(case) for case in self.__grouped_activities]
        self.set_count_encoding_df(encoded_df, np.unique(activities))
        self.set_data_value("activities", np.unique(activities).tolist())
        return ""

    def set_count_encoding_df(self, df: DataFrame, activities: np.ndarray) -> None:
        # Extract the outcome column
        outcome = df.groupby([ColumnDefinition.CASE_ID])[ColumnDefinition.OUTCOME].first().reindex()
        # Count the frequency of each activity within each group, excluding the last activity
        encoded_df = df.groupby([ColumnDefinition.CASE_ID, ColumnDefinition.ACTIVITY]).size().unstack(fill_value=0)
        # Add missing columns with 0 counts
        encoded_df = encoded_df.reindex(columns=activities, fill_value=0)
        # Merge the outcome and treatment columns back into the encoded DataFrame
        encoded_df = pd.merge(encoded_df, outcome, on=ColumnDefinition.CASE_ID)
        # Set the count encoding df
        self.__count_encoding_df = encoded_df

    def train(self) -> str:
        # Train the model
        min_length = min(self.__lengths)
        max_length = max(self.__lengths)
        threshold = 100  # The minimum number of cases needed to train the model
        models = {}
        scores = {}

        # Train the model for ordinal coding df by each length
        for length in range(min_length, max_length):
            if len([group for group in self.__grouped_activities if len(group) >= length]) < threshold:
                continue
            x = [group[:length] for group in self.__grouped_activities if len(group) >= length]
            y = [group[length - 1] for group in self.__grouped_outcomes if len(group) >= length]
            x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)
            rf = RandomForestClassifier()
            try:
                rf.fit(x_train, y_train)
            except ValueError as e:
                logger.warning(f"Training failed: {e}")
                continue
            models[length] = rf
            scores[length] = get_score(rf, x_val, y_val)

        # Train the model for count encoding df
        x = self.__count_encoding_df.drop(ColumnDefinition.OUTCOME, axis=1)
        x = x[self.get_data()["activities_code"]].values
        y = self.__count_encoding_df[ColumnDefinition.OUTCOME].values
        x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)
        rf = RandomForestClassifier()
        rf.fit(x_train, y_train)
        models["count_encoding"] = rf
        scores["count_encoding"] = get_score(rf, x_val, y_val)

        # Set the models and scores
        self.set_data_value("models", models)
        self.set_data_value("scores", scores)
        return ""

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the result
        model_and_features = get_model_and_features_by_activities(self, prefix)
        if isinstance(model_and_features, dict):
            return model_and_features
        model, features = model_and_features

        # Predict the probability of negative outcomes
        predictions = list(zip(model.classes_, model.predict_proba([features]).tolist()[0]))
        output = round(get_negative_proba(predictions), 4)
        length = len(features)
        return get_prescription_output(self, output, length, f"ordinal-encoding-length-{length}")

    def predict_df(self, df: DataFrame) -> dict:
        # Predict the result by using the given dataframe
        result = {}
        encoded_df = get_encoded_df_from_df_by_activity(self, df)
        model = self.get_data()["models"]["count_encoding"]
        predictions = model.predict_proba(encoded_df[self.get_data()["activities_code"]].values)
        # Get the result
        for case_id, prediction in zip(encoded_df.index, predictions):
            result[case_id] = get_prescription_output(
                instance=self,
                output=round(get_negative_proba(list(zip(model.classes_, prediction.tolist()))), 4),
                model_key=len(encoded_df.columns),
                model_name="count-encoding"
            )
        return result
