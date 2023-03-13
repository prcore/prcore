import logging
from typing import Tuple

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)


def get_ordinal_encoded_df(df: DataFrame, column: str) -> Tuple[DataFrame, dict]:
    # Get ordinal encoded dataframe
    df = df.copy(deep=True)
    df[column] = df[column].astype("category")
    mapping = dict(enumerate(df[column].cat.categories))
    df[column] = df[column].cat.codes
    return df, mapping
