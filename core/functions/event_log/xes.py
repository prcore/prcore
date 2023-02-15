import logging

from pandas import DataFrame
from pm4py import read_xes

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_xes(path: str) -> DataFrame:
    # Get dataframe from xes file
    df = read_xes(path)
    df_obj = df.select_dtypes(['object'])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    return df
