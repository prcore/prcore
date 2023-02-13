import logging
import requests
from multiprocessing import Event
from time import sleep

import pandas as pd
from pandas import DataFrame, read_pickle

from core.confs import config
from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_defined_column_name, get_start_timestamp
from core.functions.general.etc import random_str

# Enable logging
logger = logging.getLogger(__name__)

BASE_URL = f"http://localhost:8000"
SLEEP_INTERVAL = 5
REQUEST_HEADERS = {
    "Authorization": f"Bearer {config.API_TOKEN}",
    "Content-Type": "application/json",
}


def load_simulation_df(simulation_df_name: str) -> DataFrame:
    # Load a simulation dataframe
    return read_pickle(f"{path.EVENT_LOG_SIMULATION_DF_PATH}/{simulation_df_name}")


def preprocess_df(df: DataFrame, columns_definition: dict[str, ColumnDefinition]) -> DataFrame:
    # Preprocess a simulation dataframe
    df = df.astype(str)
    timestamp_column = get_start_timestamp(columns_definition)
    df[timestamp_column] = pd.to_datetime(df[timestamp_column], errors="coerce")
    df.sort_values(by=timestamp_column, inplace=True)
    df[timestamp_column] = df[timestamp_column].astype(str)
    case_prefix = random_str(8)
    case_id_column = get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID)
    df[case_id_column] = df[case_id_column].apply(lambda x: f"{case_prefix}-{x}")
    return df


def run_simulation(simulation_df_name: str, end_event: Event, project_id: int,
                   columns_definition: dict[str, ColumnDefinition]):
    df = load_simulation_df(simulation_df_name)
    df = preprocess_df(df, columns_definition)
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
