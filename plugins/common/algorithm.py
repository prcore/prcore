import logging
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional

from pandas import DataFrame, read_pickle, read_csv

from core.confs import path
from core.enums.definition import ColumnDefinition
from core.enums.message import MessageType
from core.functions.general.file import get_new_path
from core.functions.message.util import send_message

# Enable logging
logger = logging.getLogger(__name__)


class Algorithm:
    def __init__(self, basic_info: Dict[str, Any], project_id: int, plugin_id: Optional[int] = None,
                 df: Optional[DataFrame] = None, model_name: str = None, treatment_definition: list = None):
        self.__basic_info: Dict[str, Any] = basic_info
        self.__df: DataFrame = df
        self.__model_name: str = model_name
        self.__data = {
            "project_id": project_id,
            "plugin_id": plugin_id,
            "parameters": self.__basic_info["parameters"],
            "treatment_definition": treatment_definition
        }

    def get_basic_info(self) -> Dict[str, Any]:
        # Get basic information
        return self.__basic_info

    def get_df(self) -> DataFrame:
        # Get training data
        return self.__df

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
                self.__data = pickle.load(f)
        except Exception as e:
            logger.warning(f"Loading model failed: {e}", exc_info=True)
            return False
        return True

    def preprocess(self) -> bool:
        # Pre-process the data
        pass

    def train(self) -> bool:
        # Train the model
        pass

    def predict(self, prefix: List[dict]) -> dict:
        # Predict the next activity
        pass


def read_training_df(training_df_name: str) -> DataFrame:
    try:
        return read_pickle(f"{path.EVENT_LOG_TRAINING_DF_PATH}/{training_df_name}")
    except ValueError:
        training_csv_name = training_df_name.replace(".pkl", ".csv")
        return read_csv(f"{path.EVENT_LOG_TRAINING_DF_PATH}/{training_csv_name}")


def check_training_df(df: DataFrame, needed_columns: List[str]) -> bool:
    if ColumnDefinition.CASE_ID not in df.columns:
        return False
    if not get_timestamp_columns(df):
        return False
    if ColumnDefinition.ACTIVITY not in df.columns:
        return False
    for column in needed_columns:
        if column in {ColumnDefinition.CASE_ID,
                      ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP,
                      ColumnDefinition.ACTIVITY}:
            continue
        if column not in df.columns:
            return False
    return True


def get_timestamp_columns(df: DataFrame) -> List[str]:
    if ColumnDefinition.TIMESTAMP in df.columns:
        return [ColumnDefinition.TIMESTAMP]
    elif ColumnDefinition.START_TIMESTAMP in df.columns and ColumnDefinition.END_TIMESTAMP in df.columns:
        return [ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP]
    else:
        return []


def start_training(instance: Any) -> None:
    preprocess_result = instance.preprocess()
    if not preprocess_result:
        send_message("core", MessageType.ERROR_REPORT, get_error_data(instance, "Pre-process failed"))
    else:
        send_message(
            receiver_id="core",
            message_type=MessageType.TRAINING_START,
            data={
                "project_id": instance.get_project_id(),
                "plugin_id": instance.get_plugin_id()
            }
        )
    train_result = instance.train()
    if not train_result:
        send_message("core", MessageType.ERROR_REPORT, get_error_data(instance, "Train failed"))
    model_name = instance.save_model()
    if not model_name:
        send_message("core", MessageType.ERROR_REPORT, get_error_data(instance, "Save model failed"))
    else:
        send_message(
            receiver_id="core",
            message_type=MessageType.MODEL_NAME,
            data={
                "project_id": instance.get_project_id(),
                "plugin_id": instance.get_plugin_id(),
                "model_name": model_name
            }
        )


def get_null_output(plugin_name: str, plugin_type: str, detail: str) -> dict:
    return {
        "date": datetime.now().isoformat(),
        "type": plugin_type,
        "output": None,
        "model": {
            "name": plugin_name,
            "detail": detail
        }
    }


def get_error_data(instance: Any, detail: str) -> dict:
    return {
        "project_id": instance.get_project_id(),
        "plugin_id": instance.get_plugin_id(),
        "detail": detail
    }
