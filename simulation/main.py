import logging
import requests
from multiprocessing import Event
from time import sleep

from pandas import DataFrame, read_pickle

import core.schemas.definition as definition_schema
from core.confs import config
from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_defined_column_name, get_start_timestamp
from core.functions.event_log.dataset import get_timestamped_dataframe, get_transition_recognized_dataframe
from core.functions.general.etc import random_str

# Enable logging
logger = logging.getLogger("prcore")

BASE_URL = f"http://localhost:8000"
SLEEP_INTERVAL = 5
REQUEST_HEADERS = {
    "Authorization": f"Bearer {config.API_TOKEN}",
    "Content-Type": "application/json",
}


def load_simulation_df(simulation_df_name: str) -> DataFrame:
    # Load a simulation dataframe
    return read_pickle(f"{path.EVENT_LOG_SIMULATION_DF_PATH}/{simulation_df_name}")


def preprocess_df(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Preprocess a simulation dataframe
    # Convert all columns to string
    df = df.astype(str)
    # Convert timestamp column to datetime
    timestamp_column = get_start_timestamp(definition.columns_definition)
    df = get_timestamped_dataframe(df, definition.columns_definition)
    df = get_transition_recognized_dataframe(df, definition)
    # Sort by timestamp
    df.sort_values(by=timestamp_column, inplace=True)
    df = df.astype(str)
    # Add case prefix
    case_prefix = random_str(8)
    case_id_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)
    df[case_id_column] = df[case_id_column].apply(lambda x: f"{case_prefix}-{x}")
    # Add new column indicating the case is completed or not
    df["COMPLETE_INDICATOR"] = False
    grouped = df.groupby(case_id_column)
    df.loc[grouped.tail(1).index, "COMPLETE_INDICATOR"] = True
    return df


def run_simulation(simulation_df_name: str, end_event: Event, project_id: int,
                   definition: definition_schema.Definition):
    df = load_simulation_df(simulation_df_name)
    df = preprocess_df(df, definition)
    post_url = f"{BASE_URL}/event/{project_id}"
    for index, row in df.iterrows():
        if end_event.is_set():
            break
        response = requests.post(
            url=post_url,
            headers=REQUEST_HEADERS,
            json=row.to_dict()
        )
        print(response.json()["message"])
        sleep(5)
    end_event.set()
    print("Simulation finished")
