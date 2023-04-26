import logging
import os
import warnings
from datetime import datetime
from multiprocessing import cpu_count
from threading import Thread
from typing import Any, Dict, List

import pandas as pd
from causallift import CausalLift
from kedro.extras.datasets.pickle.pickle_dataset import PickleDataSet as PickleLocalDataSet
from pandas import DataFrame
from pandas.core.common import SettingWithCopyWarning
from sklearn.exceptions import ConvergenceWarning, UndefinedMetricWarning

from core.confs import path
from core.enums.dataset import OutcomeType
from core.enums.definition import ColumnDefinition
from core.functions.common.etc import random_str
from core.functions.common.file import delete_file
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
        proba_if_treated = round(result_df["Proba_if_Treated"].values[0].item(), 4)
        proba_if_untreated = round(result_df["Proba_if_Untreated"].values[0].item(), 4)
        cate = round(result_df["CATE"].values[0].item(), 4)
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
                "model": f"{self.get_parameter_value('encoding')}-length-{length}",
            }
        }

    def predict_df(self, df: DataFrame) -> dict:
        # Predict the result by using the given dataframe
        result = {}
        result_dfs: Dict[int, DataFrame] = {}

        # Get the test df for each length
        test_dfs, _ = get_encoded_dfs_by_activity(
            original_df=df,
            encoding_type=self.get_parameter_value("encoding"),
            outcome_type=OutcomeType.LABELLED,
            include_treatment=False,
            for_test=True,
            existing_data=self.get_data()
        )

        # Get the result for each length
        threads = []
        for length, test_df in test_dfs.items():
            training_df = self.get_data()["training_dfs"].get(length)
            if training_df is None:
                continue
            t = Thread(target=self.get_result_thread, args=(self, result_dfs, length, training_df, test_df))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Merge the result
        if len(result_dfs) <= 0:
            return result
        for length, result_df in result_dfs.items():
            treatment_definition = self.get_additional_info_value("treatment_definition")
            prescription_type = self.get_basic_info()["prescription_type"]
            plugin_name = self.get_basic_info()["name"]
            model_code = f"{self.get_parameter_value('encoding')}-length-{length}"
            for _, row in result_df.iterrows():
                case_id = self.get_case_id(row)
                proba_if_treated = round(row["Proba_if_Treated"].item(), 4)
                proba_if_untreated = round(row["Proba_if_Untreated"].item(), 4)
                cate = round(row["CATE"].item(), 4)
                output = {
                    "proba_if_treated": proba_if_treated,
                    "proba_if_untreated": proba_if_untreated,
                    "cate": cate,
                    "treatment": treatment_definition
                }
                result[case_id] = {
                    "date": datetime.now().isoformat(),
                    "type": prescription_type,
                    "output": output,
                    "plugin": {
                        "name": plugin_name,
                        "model": model_code
                    }
                }
        return result

    @staticmethod
    def get_result(training_df: DataFrame, test_df: DataFrame) -> DataFrame:
        cols_features = [x for x in training_df.columns
                         if x not in {ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT, ColumnDefinition.CASE_ID}]
        temp_dir = f"{path.TEMP_PATH}/{random_str(16)}"
        try:
            n_jobs = cpu_count() if cpu_count() <= 8 else 8
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
                ),
                uplift_model_params=dict(  # type: ignore
                    search_cv="sklearn.model_selection.GridSearchCV",
                    estimator="xgboost.XGBClassifier",
                    scoring=None,
                    cv=3,
                    return_train_score=False,
                    n_jobs=n_jobs,
                    param_grid=dict(
                        random_state=[0],
                        max_depth=[3],
                        learning_rate=[0.1],
                        n_estimators=[100],
                        verbose=[0],
                        objective=["binary:logistic"],
                        booster=["gbtree"],
                        n_jobs=[-1],
                        nthread=[None],
                        gamma=[0],
                        min_child_weight=[1],
                        max_delta_step=[0],
                        subsample=[1],
                        colsample_bytree=[1],
                        colsample_bylevel=[1],
                        reg_alpha=[0],
                        reg_lambda=[1],
                        scale_pos_weight=[1],
                        base_score=[0.5],
                        missing=[None],
                    ),
                ),
                propensity_model_params=dict(  # type: ignore
                    search_cv="sklearn.model_selection.GridSearchCV",
                    estimator="sklearn.linear_model.LogisticRegression",
                    scoring=None,
                    cv=3,
                    return_train_score=False,
                    n_jobs=n_jobs,
                    param_grid=dict(
                        random_state=[0],
                        C=[0.1, 1, 10],
                        class_weight=[None],
                        dual=[False],
                        fit_intercept=[True],
                        intercept_scaling=[1],
                        max_iter=[100],
                        multi_class=["ovr"],
                        n_jobs=[1],
                        penalty=["l1", "l2"],
                        solver=["liblinear"],
                        tol=[0.0001],
                        warm_start=[False],
                    ),
                )
            )
            _, result_df = cl.estimate_cate_by_2_models()
        finally:
            delete_file(temp_dir)
        return result_df

    @staticmethod
    def get_result_thread(self, result_dfs: Dict[int, DataFrame], length: int,
                          training_df: DataFrame, test_df: DataFrame):
        # Get the CATE using two models approach
        result_dfs[length] = self.get_result(training_df, test_df)
