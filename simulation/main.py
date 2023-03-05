import logging
from multiprocessing.synchronize import Event as ProcessEventType

import requests
from time import sleep

from pandas import DataFrame, read_pickle

import core.schemas.definition as definition_schema
from core.confs import config
from core.confs import path
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_defined_column_name
from core.functions.event_log.dataset import get_new_processed_dataframe
from core.functions.general.etc import random_str

# Enable logging
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
REQUEST_HEADERS = {
    "Authorization": f"Bearer {config.API_TOKEN}",
    "Content-Type": "application/json",
}


def load_simulation_df(simulation_df_name: str) -> DataFrame:
    # Load a simulation dataframe
    return read_pickle(f"{path.EVENT_LOG_SIMULATION_DF_PATH}/{simulation_df_name}")


def preprocess_df(df: DataFrame, definition: definition_schema.Definition) -> DataFrame:
    # Preprocess a simulation dataframe
    df = get_new_processed_dataframe(df, definition)
    # Add case prefix
    case_prefix = random_str(8)
    case_id_column = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)
    df[case_id_column] = df[case_id_column].apply(lambda x: f"{case_prefix}-{x}")
    # Add new column indicating the case is completed or not
    df[ColumnDefinition.COMPLETE_INDICATOR] = False
    grouped = df.groupby(case_id_column)
    df.loc[grouped.tail(1).index, ColumnDefinition.COMPLETE_INDICATOR] = True
    return df


def run_simulation(simulation_df_name: str, finished: ProcessEventType, project_id: int,
                   definition: definition_schema.Definition):
    df = load_simulation_df(simulation_df_name)
    df = preprocess_df(df, definition)
    post_url = f"{BASE_URL}/event/{project_id}"
    for index, row in df.iterrows():
        if finished.is_set():
            break
        response = requests.post(
            url=post_url,
            headers=REQUEST_HEADERS,
            json=row.to_dict()
        )
        logger.warning(response.json()["message"])
        sleep(config.SIMULATION_INTERVAL)
    finished.set()
    logger.warning("Simulation finished")
