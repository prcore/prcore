import datetime
import logging
from typing import Union

from pandas import read_csv, DataFrame

from core.models import PreviousEventLog
from core.models.case import Case
from core.models.event import Event
from core.models.identifier import get_identifier

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


def process_csv_file(path: str, filename: str) -> Union[PreviousEventLog, None]:
    # Process csv file
    result = None

    try:
        print("Reading csv file...")
        data = read_csv(path, sep=";")
        print("Selecting columns...")
        data = data[['Case ID', 'start_time', 'end_time', 'Activity', 'treatment']]
        print("Renaming columns...")
        data = data.rename(columns={'Case ID': 'case_id', 'start_time': 'start_timestamp', 'end_time': 'end_timestamp',
                                    'Activity': 'activity'})
        print("Converting timestamps...")
        data['start_timestamp'] = data['start_timestamp'].apply(lambda x: process_time_string(x))
        data['end_timestamp'] = data['end_timestamp'].apply(lambda x: process_time_string(x))

        cases = []
        saved_case_ids = set()

        print("Processing cases...")
        for index, row in data.iterrows():
            print(f"Processing event {index} in case {row['case_id']}...")

            if row['case_id'] not in saved_case_ids:
                new_case = Case(
                    id=get_identifier(),
                    name=f"Case {row['case_id']}",
                    status="closed",
                    events=[],
                    results=[]
                )
                new_case.save(new=True)
                cases.append(new_case)
                saved_case_ids.add(row['case_id'])

            event_dict = {
                "id": get_identifier(),
                "activity": "",
                "start_timestamp": "",
                "end_timestamp": "",
                "resource": "",
                "attributes": {}
            }

            for key in row.keys():
                if "activity" in key.lower():
                    event_dict["activity"] = row[key].strip()
                elif "start_timestamp" in key.lower():
                    event_dict["start_timestamp"] = row[key]
                elif "end_timestamp" in key.lower():
                    event_dict["end_timestamp"] = row[key]
                elif "resource" in key.lower():
                    event_dict["resource"] = row[key]
                else:
                    event_dict["attributes"][key] = row[key]

            new_event = Event(
                id=event_dict["id"],
                activity=event_dict["activity"],
                start_timestamp=event_dict["start_timestamp"],
                end_timestamp=event_dict["end_timestamp"],
                resource=event_dict["resource"],
                attributes=event_dict["attributes"]
            )
            new_event.save(new=True)
            cases[-1].events.append(new_event)

        result = PreviousEventLog(
            id=get_identifier(),
            name=filename,
            path=path,
            cases=cases
        )
    except Exception as e:
        print(e)
        logger.warning(f"Process CSV file error: {e}", exc_info=True)

    return result
