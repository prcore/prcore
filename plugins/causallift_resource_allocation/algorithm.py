import logging
import os
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from causallift import CausalLift
from kedro.extras.datasets.pickle.pickle_dataset import PickleDataSet as PickleLocalDataSet
from pandas import DataFrame
from pandas.core.common import SettingWithCopyWarning
from sklearn.exceptions import ConvergenceWarning, UndefinedMetricWarning

from core.confs import path
from core.enums.dataset import OutcomeType
from core.enums.definition import ColumnDefinition
from core.functions.common.etc import convert_to_seconds, random_str
from core.functions.common.file import delete_file
from plugins.causallift_resource_allocation import memory
from plugins.common.algorithm import Algorithm
from plugins.common.dataset import get_encoded_dfs_by_activity

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
        self.__training_dfs: Dict[int, DataFrame] = {}

    def preprocess(self) -> str:
        # Pre-process the data
        self.__training_dfs, data = get_encoded_dfs_by_activity(
            original_df=self.get_df(),
            encoding_type=self.get_parameter_value("encoding"),
            outcome_type=OutcomeType.LABELLED,
            include_treatment=True,
            for_test=False,
            existing_data={}
        )
        for key in data:
            if key in {"mapping", "lb"}:
                self.set_data_value(key, data[key])
        return ""

    def train(self) -> str:
        # Train the model
        self.set_data_value("training_dfs", self.__training_dfs)
        return ""

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the result by using the given prefix
        available_resources = self.get_additional_info_value("available_resources")
        treatment_duration = convert_to_seconds(self.get_additional_info_value("treatment_duration"))
        if not available_resources or not treatment_duration:
            return self.get_null_output("The available resources or the treatment duration is not provided")

        length = len(prefix)
        training_df = self.get_data()["training_dfs"].get(length)
        if training_df is None:
            return self.get_null_output("The model is not trained for the given prefix length")

        # Get the test df
        raw_test_df = pd.DataFrame(prefix)
        test_df = list(get_encoded_dfs_by_activity(
            original_df=raw_test_df,
            encoding_type=self.get_parameter_value("encoding"),
            outcome_type=OutcomeType.LABELLED,
            include_treatment=False,
            for_test=True,
            existing_data=self.get_data()
        )[0].values())[0]

        # Get the CATE using two models approach
        result_df = self.get_result(training_df, test_df)
        cate = round(result_df["CATE"].values[0].item(), 4)
        resource_allocation = self.get_resource_allocation_result(available_resources, treatment_duration, cate)
        resource = resource_allocation["resource"]
        detail = resource_allocation["detail"]
        if not resource:
            return self.get_null_output(detail)
        return {
            "date": datetime.now().isoformat(),
            "type": self.get_basic_info()["prescription_type"],
            "output": {
                "cate": cate,
                "resource": resource,
                "allocated_until": detail.isoformat()
            },
            "plugin": {
                "name": self.get_basic_info()["name"],
                "model": f"{self.get_parameter_value('encoding')}-length-{length}",
            }
        }

    def predict_df(self, df: DataFrame) -> dict:
        # Predict the result by using the given dataframe
        return {}

    @staticmethod
    def get_result(training_df: DataFrame, test_df: DataFrame) -> DataFrame:
        cols_features = [x for x in training_df.columns
                         if x not in {ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT, ColumnDefinition.CASE_ID}]
        temp_dir = f"{path.TEMP_PATH}/{random_str(16)}"
        try:
            cl = CausalLift(
                train_df=training_df,
                test_df=test_df,
                enable_ipw=True,
                logging_config=None,
                cols_features=cols_features,
                col_treatment=ColumnDefinition.TREATMENT,
                col_outcome=ColumnDefinition.OUTCOME, verbose=0,
                dataset_catalog=dict(
                    propensity_model=PickleLocalDataSet(
                        filepath=f"{temp_dir}/propensity_model.pickle",
                        version=None
                    ),
                    uplift_models_dict=PickleLocalDataSet(
                        filepath=f"{temp_dir}/uplift_models_dict.pickle",
                        version=None
                    )
                )
            )
            _, result_df = cl.estimate_cate_by_2_models()
        finally:
            delete_file(temp_dir)
        return result_df

    def get_resource_allocation_result(self, available_resources: List[str], treatment_duration: int,
                                       cate: float) -> dict:
        # Get the resource allocation result
        if cate <= 0:
            return {
                "resource": None,
                "detail": "The CATE is less than or equal to 0, so no resource allocation is needed"
            }
        project_id = self.get_data()["project_id"]
        selected_resource = self.select_resource(project_id, available_resources, treatment_duration)
        if selected_resource is None:
            return {
                "resource": None,
                "detail": "There is no available resource"
            }
        return {
            "resource": selected_resource,
            "detail": memory.resources[project_id][selected_resource]
        }

    @staticmethod
    def select_resource(project_id: int, available_resources: List[str], treatment_duration: int) -> Optional[str]:
        if memory.resources.get(project_id) is None:
            memory.resources[project_id] = {}
        allocated_resource = memory.resources.get(project_id)
        now = datetime.now()
        for resource in available_resources:
            if resource in allocated_resource:
                available_since = allocated_resource[resource]
                if now <= available_since:
                    continue
                memory.resources[project_id][resource] = now + timedelta(seconds=treatment_duration)
                return resource
            else:
                memory.resources[project_id][resource] = now + timedelta(seconds=treatment_duration)
                return resource
        return None
