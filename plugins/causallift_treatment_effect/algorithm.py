import logging
import os
import warnings
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from causallift import CausalLift
from pandas import DataFrame
from pandas.core.common import SettingWithCopyWarning
from sklearn.exceptions import ConvergenceWarning, UndefinedMetricWarning
from sklearn.preprocessing import LabelBinarizer

from core.enums.definition import ColumnDefinition
from core.functions.training.util import get_ordinal_encoded_df
from plugins.common.algorithm import Algorithm, get_null_output, get_encoded_df_from_df_by_activity
from plugins.common.dataset import get_boolean_encoding_dataframes_by_length

# Enable logging
logger = logging.getLogger(__name__)

# Ignore warnings caused by the causallift package itself
warnings.simplefilter("ignore", category=DeprecationWarning)
warnings.simplefilter("ignore", category=ConvergenceWarning)
warnings.simplefilter("ignore", category=SettingWithCopyWarning)
warnings.simplefilter("ignore", category=UndefinedMetricWarning)
os.environ["PYTHONWARNINGS"] = "ignore"


class CausalLiftAlgorithm(Algorithm):
    def __init__(self, algo_data: Dict[str, Any]):
        super().__init__(algo_data)
        self.__grouped_activities = []
        self.__grouped_outcomes = []
        self.__grouped_treatments = []
        self.__lengths = []
        self.__one_hot_dataframes = {}

    def preprocess(self) -> str:
        # Pre-process the data
        encoded_df, mapping = get_ordinal_encoded_df(self.get_df(), ColumnDefinition.ACTIVITY)
        self.set_data_value("mapping", {v: k for k, v in mapping.items()})
        case_ids = encoded_df[ColumnDefinition.CASE_ID].values
        activities = encoded_df[ColumnDefinition.ACTIVITY].values
        outcomes = encoded_df[ColumnDefinition.OUTCOME].values
        treatments = encoded_df[ColumnDefinition.TREATMENT].values
        unique_case_ids = np.unique(case_ids)
        self.__grouped_activities = [activities[case_ids == case_id] for case_id in unique_case_ids]
        self.__grouped_outcomes = [outcomes[case_ids == case_id][0] for case_id in unique_case_ids]
        self.__grouped_treatments = [treatments[case_ids == case_id][0] for case_id in unique_case_ids]
        self.__lengths = [len(case) for case in self.__grouped_activities]
        self.set_data_value("activities", np.unique(activities).tolist())
        return ""

    def train(self) -> str:
        # Train the model
        min_length = min(self.__lengths) if min(self.__lengths) < 3 else 3
        max_length = max(self.__lengths)
        threshold = 1000  # The minimum number of cases needed to train the model
        training_dfs = {}

        # Get the training data for ordinal coding df by each length
        for length in range(min_length, max_length):
            if len([group for group in self.__grouped_activities if len(group) > length]) < threshold:
                continue
            training_data = []
            for i, group in enumerate(self.__grouped_activities):
                if len(group) <= length:
                    continue
                x = group[:length]
                y = self.__grouped_outcomes[i]
                t = self.__grouped_treatments[i]
                training_data.append([x, y, t])
            training_df = pd.DataFrame(
                data=training_data,
                columns=["EVENTS", ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]
            )
            activities_df = pd.DataFrame(
                data=np.stack(training_df["EVENTS"], axis=0),
                columns=[f"EVENT_{i}" for i in range(length)]
            )
            training_df = pd.concat(
                objs=[activities_df, training_df[[ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT]]],
                axis=1
            )
            if training_df[ColumnDefinition.TREATMENT].nunique() != 2:
                continue
            training_dfs[length] = training_df

        self.set_data_value("training_dfs", training_dfs)
        return ""

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the result by using the given prefix
        if any(x["ACTIVITY"] not in self.get_data()["mapping"] for x in prefix):
            return get_null_output(self, "The prefix contains an activity that is not in the training set")

        # Get the length of the prefix
        length = len(prefix)
        training_df = self.get_data()["training_dfs"].get(length)
        if training_df is None:
            return get_null_output(self, "The model is not trained for the given prefix length")

        # Get the features of the prefix
        features = [self.get_data()["mapping"][x["ACTIVITY"]] for x in prefix]

        # Get the CATE using two models approach
        test_df = DataFrame([features], columns=[f"EVENT_{i}" for i in range(length)])
        cl = CausalLift(train_df=training_df, test_df=test_df, enable_ipw=True, logging_config=None,
                        col_treatment=ColumnDefinition.TREATMENT, col_outcome=ColumnDefinition.OUTCOME, verbose=0)
        train_df, test_df = cl.estimate_cate_by_2_models()
        proba_if_treated = round(test_df["Proba_if_Treated"].values[0].item(), 4)
        proba_if_untreated = round(test_df["Proba_if_Untreated"].values[0].item(), 4)
        cate = round(test_df["CATE"].values[0].item(), 4)

        output = {
            "proba_if_treated": proba_if_treated,
            "proba_if_untreated": proba_if_untreated,
            "cate": cate,
            "treatment": self.get_additional_info_value("treatment_definition")
        }
        return {
            "date": datetime.now().isoformat(),
            "type": self.get_basic_info()["prescription_type"],
            "output": output,
            "plugin": {
                "name": self.get_basic_info()["name"],
                "model": length
            }
        }

    def predict_df(self, df: DataFrame) -> dict:
        # Predict the result by using the given dataframe
        result = {}
        encoded_df = get_encoded_df_from_df_by_activity(self, df)
        training_df = self.get_data()["training_dfs"]["count_encoding"]
        # Convert columns name to string
        encoded_df.columns = encoded_df.columns.astype(str)
        training_df.columns = training_df.columns.astype(str)
        # Get the CATE using two models approach
        cl = CausalLift(train_df=training_df, test_df=encoded_df, enable_ipw=True, logging_config=None,
                        col_treatment=ColumnDefinition.TREATMENT, col_outcome=ColumnDefinition.OUTCOME)
        train_df, test_df = cl.estimate_cate_by_2_models()
        # Get the result
        for case_id, p in zip(encoded_df.index, test_df.values):
            proba_if_treated = round(p[-3].item(), 4)
            proba_if_untreated = round(p[-2].item(), 4)
            cate = round(p[-1].item(), 4)
            output = {
                "proba_if_treated": proba_if_treated,
                "proba_if_untreated": proba_if_untreated,
                "cate": cate,
                "treatment": self.get_additional_info_value("treatment_definition")
            }
            result[case_id] = {
                "date": datetime.now().isoformat(),
                "type": self.get_basic_info()["prescription_type"],
                "output": output,
                "plugin": {
                    "name": self.get_basic_info()["name"],
                    "model": "count-encoding"
                }
            }
        return result

    def preprocess_one_hot(self) -> str:
        # Pre-process the data
        self.__one_hot_dataframes = get_boolean_encoding_dataframes_by_length(self.get_df())
        activities = sorted(set(self.get_df()[ColumnDefinition.ACTIVITY]))
        self.set_data_value("activities", activities)
        return ""

    def train_one_hot(self) -> str:
        # Train the model
        training_dfs = {}
        for length, df in self.__one_hot_dataframes.items():
            training_dfs[length] = df
        self.set_data_value("training_dfs", training_dfs)
        return ""

    def train_one_hot_faster(self) -> str:
        # Train the model
        min_length = min(self.__lengths) if min(self.__lengths) > 3 else 3
        max_length = max(self.__lengths)
        threshold = 1000  # The minimum number of cases needed to train the model
        training_dfs = {}

        from datetime import datetime
        start_time = datetime.now()

        activities = self.get_data()["activities"]
        lb = LabelBinarizer()
        lb.fit(activities)

        # Get the training data for ordinal coding df by each length
        for length in range(min_length, max_length):
            if len([group for group in self.__grouped_activities if len(group) > length]) < threshold:
                continue
            training_data = []
            for i, group in enumerate(self.__grouped_activities):
                if len(group) < length:
                    continue
                x_raw = group[:length]
                arr_encoded = lb.transform(x_raw)
                arr_sum = arr_encoded.sum(axis=0)
                x = np.where(arr_sum > 0, 1, 0)
                y = self.__grouped_outcomes[i]
                t = self.__grouped_treatments[i]
                training_data.append([x, y, t])
            training_df = pd.DataFrame(training_data, columns=["Activities", "Outcome", "Treatment"])
            activities_df = pd.DataFrame(np.stack(training_df["Activities"], axis=0),
                                         columns=lb.classes_.tolist())
            training_df = pd.concat([activities_df, training_df[["Outcome", "Treatment"]]], axis=1)
            if training_df["Treatment"].nunique() != 2:
                continue
            training_dfs[length] = training_df

        end_time = datetime.now()
        print('Time taken: {}'.format(end_time - start_time))

        self.set_data_value("training_dfs", training_dfs)
        return ""

    def predict_one_hot(self, prefix: List[dict]) -> dict:
        # Predict the result by using the given prefix
        activities = self.get_data()["activities"]
        if any(x[ColumnDefinition.ACTIVITY] not in activities for x in prefix):
            return get_null_output(self, "The prefix contains an activity that is not in the training set")

        # Get the length of the prefix
        length = len(prefix)
        training_df = self.get_data()["training_dfs"].get(length)
        if training_df is None:
            return get_null_output(self, "The model is not trained for the given prefix length")

        # Get the features of the prefix
        prefix_activities = {x[ColumnDefinition.ACTIVITY] for x in prefix}
        features = [1 if x in prefix_activities else 0 for x in activities]
        columns = [f"{ColumnDefinition.ACTIVITY}_{x}" for x in activities]
        test_df = DataFrame([features], columns=columns)
        training_df_activities_columns = [x for x in training_df.columns if x.startswith(ColumnDefinition.ACTIVITY)]
        test_df = test_df[training_df_activities_columns]

        # Get the CATE using two models approach
        cl = CausalLift(
            train_df=training_df,
            test_df=test_df,
            enable_ipw=True,
            col_treatment=ColumnDefinition.TREATMENT,
            col_outcome=ColumnDefinition.OUTCOME,
            logging_config=None
        )
        train_df, test_df = cl.estimate_cate_by_2_models()
        proba_if_treated = round(test_df["Proba_if_Treated"].values[0].item(), 4)
        proba_if_untreated = round(test_df["Proba_if_Untreated"].values[0].item(), 4)
        cate = round(test_df["CATE"].values[0].item(), 4)

        output = {
            "proba_if_treated": proba_if_treated,
            "proba_if_untreated": proba_if_untreated,
            "cate": cate,
            "treatment": self.get_additional_info_value("treatment_definition")
        }
        return {
            "date": datetime.now().isoformat(),
            "type": self.get_basic_info()["prescription_type"],
            "output": output,
            "plugin": {
                "name": self.get_basic_info()["name"],
                "model": length
            }
        }
