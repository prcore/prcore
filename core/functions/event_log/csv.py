import datetime
import logging

from pandas import read_csv, DataFrame

# Enable logging
logger = logging.getLogger(__name__)


def get_dataframe_from_csv(path: str, seperator: str) -> DataFrame:
    # Get dataframe from csv file
    df = read_csv(path, sep=seperator)
    df_obj = df.select_dtypes(['object'])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    return df


def process_time_string(time_string: str) -> int:
    # Process time string
    result = 0

    try:
        time_string = time_string.replace("T", " ")
        time_string = time_string.split(".")[0]
        result = int(datetime.datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S').timestamp())
    except Exception as e:
        print(e)
        logger.warning(f"Process time string error: {e}", exc_info=True)

    return result
