import logging
from typing import Any, Dict, List

import pandas as pd
from pandas import DataFrame
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

from core.enums.dataset import OutcomeType
from core.enums.definition import ColumnDefinition
from plugins.common.algorithm import Algorithm
from plugins.common.dataset import get_encoded_dfs_by_activity

# Enable logging
logger = logging.getLogger(__name__)


class KNNAlgorithm(Algorithm):
    def __init__(self, algo_data: Dict[str, Any]):
        super().__init__(algo_data)
        self.__training_dfs: Dict[int, DataFrame] = {}

    def preprocess(self) -> str:
        # Pre-process the data
        self.__training_dfs, data = get_encoded_dfs_by_activity(
            original_df=self.get_df(),
            encoding_type=self.get_parameter_value("encoding"),
            outcome_type=OutcomeType.LAST_ACTIVITY,
            include_treatment=False,
            for_test=False,
            existing_data={}
        )
        for key in data:
            if key in {"mapping", "lb"}:
                self.set_data_value(key, data[key])
        return ""

    def train(self) -> str:
        # Train the model
        models = {}
        scores = {}
        for length in self.__training_dfs:
            df = self.__training_dfs[length]
            x = df.drop([ColumnDefinition.OUTCOME, ColumnDefinition.CASE_ID], axis=1)
            y = df[ColumnDefinition.OUTCOME]
            x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)
            knn = KNeighborsClassifier(n_neighbors=self.get_parameter_value("n_neighbors"))
            knn.fit(x_train, y_train)
            models[length] = knn
            scores[length] = self.get_score(knn, x_val, y_val)
        self.set_data_value("models", models)
        self.set_data_value("scores", scores)
        return ""

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the result by using the given prefix
        length = len(prefix)
        model = self.get_data()["models"].get(length)
        if model is None:
            return self.get_null_output("The model is not trained for the given prefix length")

        # Get the test df
        raw_test_df = pd.DataFrame(prefix)
        test_df = list(get_encoded_dfs_by_activity(
            original_df=raw_test_df,
            encoding_type=self.get_parameter_value("encoding"),
            outcome_type=OutcomeType.LAST_ACTIVITY,
            include_treatment=False,
            for_test=True,
            existing_data=self.get_data()
        )[0].values())[0]

        # Predict the next activity
        prediction = model.predict(test_df.drop([ColumnDefinition.CASE_ID], axis=1))[0]
        reversed_mapping = {v: k for k, v in self.get_data()["mapping"].items()}
        output = reversed_mapping.get(prediction, "Unknown")
        return self.get_prescription_output(output, length, f"{self.get_parameter_value('encoding')}-length-{length}")

    def predict_df(self, df: DataFrame) -> dict:
        # Predict the result by using the given dataframe
        result = {}
        reversed_mapping = {v: k for k, v in self.get_data()["mapping"].items()}

        # Get the test df for each length
        test_dfs, _ = get_encoded_dfs_by_activity(
            original_df=df,
            encoding_type=self.get_parameter_value("encoding"),
            outcome_type=OutcomeType.LAST_ACTIVITY,
            include_treatment=False,
            for_test=True,
            existing_data=self.get_data()
        )

        # Get the result for each length
        for length, test_df in test_dfs.items():
            model = self.get_data()["models"].get(length)
            if model is None:
                continue
            predictions = model.predict(test_df.drop([ColumnDefinition.CASE_ID], axis=1))
            outputs = [reversed_mapping.get(prediction, "Unknown") for prediction in predictions]
            for i in range(len(test_df)):
                case_id = test_df.iloc[i][ColumnDefinition.CASE_ID]
                output = outputs[i]
                result[case_id] = self.get_prescription_output(
                    output=output,
                    model_key=length,
                    model_code=f"{self.get_parameter_value('encoding')}-length-{length}"
                )

        return result
