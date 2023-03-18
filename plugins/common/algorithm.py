import logging
import pickle
from datetime import datetime
from typing import Any, Dict, List, Union

from pandas import DataFrame, Series
from sklearn.metrics import precision_score, recall_score, f1_score

from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.common.file import get_new_path

# Enable logging
logger = logging.getLogger(__name__)


class Algorithm:
    def __init__(self, algo_data: Dict[str, Any]):
        self.__basic_info: Dict[str, Any] = algo_data.get("basic_info")
        self.__project_id: int = algo_data.get("project_id")
        self.__plugin_id: int = algo_data.get("plugin_id")
        self.__df: DataFrame = algo_data.get("df")
        self.__parameters: Dict[str, Any] = algo_data.get("parameters")
        self.__additional_info: Dict[str, Any] = algo_data.get("additional_info")
        self.__model_name: str = algo_data.get("model_name")
        self.__data = {
            "project_id": self.__project_id,
            "plugin_id": self.__plugin_id,
            "parameters": self.__parameters
        }

    def get_basic_info(self) -> Dict[str, Any]:
        # Get basic information
        return self.__basic_info

    def get_df(self) -> DataFrame:
        # Get training data
        return self.__df

    def get_parameter_value(self, key: str) -> Any:
        # Get parameter value
        return self.__data["parameters"].get(key)

    def get_additional_info_value(self, key: str) -> Any:
        # Get additional information
        return self.__additional_info.get(key)

    def set_additional_info(self, additional_info: Dict[str, Any]):
        # Set additional information
        self.__additional_info = additional_info

    def get_data(self) -> Dict[str, Any]:
        # Get data
        return self.__data

    def set_data_value(self, key: str, value: Any):
        # Set data value
        self.__data[key] = value

    def get_project_id(self) -> int:
        # Get project ID
        return self.__data["project_id"]

    def get_plugin_id(self) -> int:
        # Get plugin ID
        return self.__data["plugin_id"]

    def save_model(self) -> str:
        # Save the model
        result = ""
        try:
            model_path = get_new_path(f"{path.PLUGIN_MODEL_PATH}/", suffix=".pkl")
            with open(model_path, "wb") as f:
                pickle.dump(self.__data, f)
            result = model_path.split("/")[-1]
        except Exception as e:
            logger.warning(f"Saving model failed: {e}", exc_info=True)
        return result

    def load_model(self) -> bool:
        # Load the model
        if self.__data.get("models"):
            return True
        if not self.__model_name:
            return False
        try:
            with open(f"{path.PLUGIN_MODEL_PATH}/{self.__model_name}", "rb") as f:
                self.__data = pickle.load(f)  # nosec B301
        except Exception as e:
            logger.warning(f"Loading model failed: {e}", exc_info=True)
            return False
        return True

    def preprocess(self) -> str:
        # Pre-process the data
        pass

    def train(self) -> str:
        # Train the model
        pass

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the result by using the given prefix
        pass

    def predict_df(self, df: DataFrame) -> dict:
        # Predict the result using a DataFrame
        pass

    @staticmethod
    def get_case_id(row: Series) -> str:
        case_id = row[ColumnDefinition.CASE_ID].item()
        if isinstance(case_id, str):
            return case_id
        case_id = str(case_id)
        if case_id.endswith(".0"):
            case_id = case_id[:-2]
        return case_id

    def get_null_output(self, detail: str) -> dict:
        return {
            "date": datetime.now().isoformat(),
            "type": self.get_basic_info()["prescription_type"],
            "output": None,
            "model": {
                "name": self.get_basic_info()["name"],
                "detail": detail
            }
        }

    @staticmethod
    def get_score(model, x_val, y_val) -> dict:
        # Get the score of the model
        y_pred = model.predict(x_val)
        accuracy = round(model.score(x_val, y_val), 4)
        precision = round(precision_score(y_val, y_pred, average="weighted", zero_division=1), 4)
        recall = round(recall_score(y_val, y_pred, average="weighted", zero_division=1), 4)
        f1 = round(f1_score(y_val, y_pred, average="weighted"), 4)
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

    def get_prescription_output(self, output: Any, model_key: Union[int, str], model_code: str) -> dict:
        return {
            "date": datetime.now().isoformat(),
            "type": self.get_basic_info()["prescription_type"],
            "output": output,
            "plugin": {
                "name": self.get_basic_info()["name"],
                "model": model_code,
                **self.get_data()["scores"][model_key]
            }
        }
