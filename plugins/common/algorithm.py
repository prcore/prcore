import logging
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pandas import DataFrame, read_pickle, read_csv
from sklearn.metrics import precision_score, recall_score, f1_score

from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.general.file import get_new_path

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

    def get_parameter_value(self, key: str) -> Any:
        # Get parameter value
        return self.__data["parameters"][key]

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


def read_df_from_path(directory: str, df_name: str) -> DataFrame:
    try:
        return read_pickle(f"{directory}/{df_name}.pkl")
    except ValueError:
        # If the plugin's Python version is 3.6, then the pickle protocol is not compatible,
        # so we need to read the CSV file
        return read_csv(f"{directory}/{df_name}.csv")


def check_training_df(df: DataFrame, needed_columns: List[str]) -> Union[str, bool]:
    # Basic check
    if (ColumnDefinition.CASE_ID not in df.columns
            or not get_timestamp_columns(df)
            or ColumnDefinition.ACTIVITY not in df.columns):
        return False

    # Check if all needed columns are in the df
    for column in needed_columns:
        if column in {ColumnDefinition.CASE_ID,
                      ColumnDefinition.TIMESTAMP, ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP,
                      ColumnDefinition.ACTIVITY}:
            continue
        if column not in df.columns:
            return False

    # Check if the df has only two classes for outcome and treatment
    for column in {ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT}:
        if column in needed_columns and column in df.columns and df[column].nunique() != 2:
            return f"The {column} column must have two classes, please adjust your {column.lower()} definition"

    return True


def get_timestamp_columns(df: DataFrame) -> List[str]:
    if ColumnDefinition.TIMESTAMP in df.columns:
        return [ColumnDefinition.TIMESTAMP]
    elif ColumnDefinition.START_TIMESTAMP in df.columns and ColumnDefinition.END_TIMESTAMP in df.columns:
        return [ColumnDefinition.START_TIMESTAMP, ColumnDefinition.END_TIMESTAMP]
    else:
        return []


def get_encoded_df_from_df_by_activity(instance: Algorithm, df: DataFrame) -> DataFrame:
    # Map the activities to the ordinal encoding
    df[ColumnDefinition.ACTIVITY] = df[ColumnDefinition.ACTIVITY].map(instance.get_data()["mapping"])
    # Drop the rows with NaN values in the activity column
    df = df.dropna(subset=[ColumnDefinition.ACTIVITY])
    # Convert the dataframe to the count encoding dataframe
    encoded_df = df.groupby([ColumnDefinition.CASE_ID, ColumnDefinition.ACTIVITY]).size().unstack(fill_value=0)
    encoded_df = encoded_df.reindex(columns=instance.get_data()["activities"], fill_value=0)
    return encoded_df


def get_model_and_features_by_activities(instance: Algorithm, prefix: List[dict]) -> Union[dict, tuple]:
    # Predict the result
    if any(x["ACTIVITY"] not in instance.get_data()["mapping"] for x in prefix):
        return get_null_output(instance.get_basic_info()["name"], instance.get_basic_info()["prescription_type"],
                               "The prefix contains an activity that is not in the training set")

    # Get the length of the prefix
    length = len(prefix)
    model = instance.get_data()["models"].get(length)
    if not model:
        return get_null_output(instance.get_basic_info()["name"], instance.get_basic_info()["prescription_type"],
                               "The model is not trained for the given prefix length")

    # Get the features of the prefix
    features = [instance.get_data()["mapping"][x["ACTIVITY"]] for x in prefix]
    return model, features


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


def get_prescription_output(instance: Algorithm, output: Any, model_key: Union[int, str], model_name: str) -> dict:
    return {
        "date": datetime.now().isoformat(),
        "type": instance.get_basic_info()["prescription_type"],
        "output": output,
        "plugin": {
            "name": instance.get_basic_info()["name"],
            "model": model_name,
            **instance.get_data()["scores"][model_key]
        }
    }
