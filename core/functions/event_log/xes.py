import logging

from pandas import DataFrame
from pm4py import read_xes

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_xes(path: str) -> DataFrame:
    # Get dataframe from xes file
    return read_xes(path)
