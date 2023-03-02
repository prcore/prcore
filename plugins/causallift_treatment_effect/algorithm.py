import logging
import pickle
from datetime import datetime
from typing import List, Union

import numpy as np
import pandas as pd
from causallift import CausalLift
from pandas import DataFrame

from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.general.file import get_new_path
from core.functions.training.util import get_ordinal_encoded_df

from plugins.common.algorithm import get_null_output
from plugins.causallift_treatment_effect.config import basic_info

# Enable logging
logger = logging.getLogger(__name__)


class Algorithm:
    def __init__(self, project_id: int, plugin_id: Union[int, None], df: Union[DataFrame, None], model_name: str = None,
                 parameters: dict = basic_info["parameters"], treatment_definition: list = None):
        self.df: DataFrame = df
        self.model_name: str = model_name
        self.parameters: dict = parameters
        self.grouped_activities = []
        self.grouped_outcomes = []
        self.grouped_treatments = []
        self.lengths = []
        self.data = {
            "project_id": project_id,
            "plugin_id": plugin_id,
            "training_dfs": {},
            "mapping": {},
            "treatment_definition": treatment_definition
        }

    def get_project_id(self) -> int:
        return self.data["project_id"]

    def get_plugin_id(self) -> int:
        return self.data["plugin_id"]

    def preprocess(self) -> bool:
        # Pre-process the data
        try:
            encoded_df, mapping = get_ordinal_encoded_df(self.df, ColumnDefinition.ACTIVITY)
            self.data["mapping"] = {v: k for k, v in mapping.items()}
            case_ids = encoded_df[ColumnDefinition.CASE_ID].values
            activities = encoded_df[ColumnDefinition.ACTIVITY].values
            outcomes = encoded_df[ColumnDefinition.OUTCOME].values
            treatments = encoded_df[ColumnDefinition.TREATMENT].values
            unique_case_ids = np.unique(case_ids)
            self.grouped_activities = [activities[case_ids == case_id] for case_id in unique_case_ids]
            self.grouped_outcomes = [outcomes[case_ids == case_id][0] for case_id in unique_case_ids]
            self.grouped_treatments = [treatments[case_ids == case_id][0] for case_id in unique_case_ids]
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
                training_data = []
                for i, group in enumerate(self.grouped_activities):
                    if len(group) < length:
                        continue
                    x = group[:length]
                    y = self.grouped_outcomes[i]
                    t = self.grouped_treatments[i]
                    training_data.append([x, y, t])
                training_df = pd.DataFrame(training_data, columns=["Activities", "Outcome", "Treatment"])
                activities_df = pd.DataFrame(np.stack(training_df["Activities"], axis=0),
                                             columns=[f"Activity_{i}" for i in range(length)])
                training_df = pd.concat([activities_df, training_df[["Outcome", "Treatment"]]], axis=1)
                self.data["training_dfs"][length] = training_df
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
        if self.data["training_dfs"]:
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

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the next activity
        if any(x["ACTIVITY"] not in self.data["mapping"] for x in prefix):
            return get_null_output(basic_info["name"], basic_info["prescription_type"],
                                   "The prefix contains an activity that is not in the training set")

        # Get the length of the prefix
        length = len(prefix)
        training_df = self.data["training_dfs"].get(length)
        if training_df is None:
            return get_null_output(basic_info["name"], basic_info["prescription_type"],
                                   "The model is not trained for the given prefix length")

        # Get the features of the prefix
        features = [self.data["mapping"][x["ACTIVITY"]] for x in prefix]

        # Get the CATE using two models approach
        test_df = DataFrame([features], columns=[f"Activity_{i}" for i in range(length)])
        cl = CausalLift(train_df=training_df, test_df=test_df, enable_ipw=True, logging_config=None)
        train_df, test_df = cl.estimate_cate_by_2_models()
        proba_if_treated = round(test_df["Proba_if_Treated"].values[0].item(), 4)
        proba_if_untreated = round(test_df["Proba_if_Untreated"].values[0].item(), 4)
        cate = round(test_df["CATE"].values[0].item(), 4)

        output = {
            "proba_if_treated": proba_if_treated,
            "proba_if_untreated": proba_if_untreated,
            "cate": cate,
            "treatment": self.data["treatment_definition"]
        }
        return {
            "date": datetime.now().isoformat(),
            "type": basic_info["prescription_type"],
            "output": output,
            "plugin": {
                "name": basic_info["name"],
                "model": length
            }
        }

    def set_parameters(self, parameters):
        # Set the parameters of the algorithm
        self.parameters = parameters
