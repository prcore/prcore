import datetime
import json
import requests
from time import sleep
from random import choice
from pandas import read_csv, DataFrame

from pm4py import read_xes

TEST_MODE = 'csv'
SLEEP_TIME = 5
ID_OFFSET = 8000000
CSV_DATASET_PATH = "../data/datasets/prepared_treatment_outcome_bpic2012.csv"
CSV_DELIMITER = ";"
XES_DATASET_PATH = "../data/datasets/OrderFullfilment.xes"
TEST_DATASET_PATH = "../data/datasets/test_cases.json"
THE_SPLIT = 0.8
DASHBOARD_ID = 126697
SENDING_MODE = "single"


def process_time_string(time_string: str) -> int:
    # Process time string
    result = 0

    try:
        time_string = time_string.replace("T", " ")
        time_string = time_string.split(".")[0]
        result = int(datetime.datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S').timestamp())
    except Exception as e:
        print(e)

    return result


def load_xes_file(path):
    event_log = read_xes(path)

    if not event_log:
        print("File not valid")

    return event_log


def load_csv_file(path) -> DataFrame:
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
    return data


def get_all_cases_from_event_log(event_log):
    cases = {}

    for i in range(len(event_log)):
        case_id = ID_OFFSET + i
        cases[case_id] = get_all_events_from_event_log(case_id, event_log[i])

    return cases


def get_all_cases_from_dataframe(data: DataFrame) -> dict:
    # Get all cases from the dataframe
    cases = {}
    saved_case_id = set()
    i = 0

    for index, row in data.iterrows():  # noqa
        old_case_id = row["case_id"]

        if old_case_id not in saved_case_id:
            case_id = i + ID_OFFSET
            cases[case_id] = []
            i += 1
            saved_case_id.add(old_case_id)
        else:
            case_id = list(cases.keys())[-1]

        event = row.to_dict()
        event["activity"] = event["activity"].strip()
        event["case_id"] = case_id
        event["attributes"] = {}
        event["attributes"]["treatment"] = event["treatment"]
        cases[case_id].append(event)

    return cases


def get_all_events_from_event_log(case_id, case):
    events = []
    for j in case:
        should_pass = False
        event_dict = {
            "case_id": case_id,
            "activity": "",
            "timestamp": "",
            "resource": "",
            "attributes": {}
        }
        for key in j:
            if key == "lifecycle:transition" and j[key] != "complete":
                should_pass = True
                continue
            if "activity" in key.lower() or "concept:name" in key.lower():
                event_dict["activity"] = j[key]
            elif "timestamp" in key.lower():
                event_dict["timestamp"] = str(j[key])
            elif "resource" in key.lower():
                event_dict["resource"] = j[key]
            else:
                event_dict["attributes"][key] = j[key]
        if should_pass:
            continue
        events.append(event_dict)

    return events


def get_test_cases(cases: dict):
    # Get the test cases: test part of the cases
    test_cases = {}
    print(f"Length of cases: {len(cases)}")
    print(f"First 10 cases: {list(cases.keys())[:10]}")
    print(f"Last 10 cases: {list(cases.keys())[-10:]}")
    for i in range(int(len(cases) * THE_SPLIT), len(cases)):  # noqa
        test_cases[i + ID_OFFSET] = cases[i + ID_OFFSET]
    return test_cases


def write_cases_to_json_file(cases: dict, path: str):
    # Write to json file with indent 4
    with open(path, "w") as file:
        json.dump(cases, file, indent=4)


def call_post_api_for_cases(cases: dict):
    cases_keys = set(cases.keys())

    while len(cases_keys) > 0:
        case_id = choice(list(cases_keys))
        case = cases[case_id]

        if SENDING_MODE == "random":
            event = case[0]
            event["dashboard_id"] = DASHBOARD_ID
            event.pop("treatment", None)
            event["status"] = "closed" if len(case) == 1 else "ongoing"
            print(f"Sending the event: {json.dumps(event, indent=4)}")
            requests.post("http://localhost:8000/event", json=event)
            print("Event sent!")

            if len(case) == 1:
                cases_keys.discard(case_id)
            else:
                cases[case_id] = case[1:]

            sleep(SLEEP_TIME)
        else:
            for event in case:
                event["dashboard_id"] = DASHBOARD_ID
                event.pop("treatment", None)

                if len(case) == 1:
                    print("Test completed since the mode is Singleton")
                    break

                event["status"] = "closed" if len(case) == 1 else "ongoing"
                print(f"Sending the event: {json.dumps(event, indent=4)}")
                requests.post("http://localhost:8000/event", json=event)
                print("Event sent!")

                cases[case_id] = case[1:]
                sleep(SLEEP_TIME + 3)


def get_test_cases_under_xes_mode() -> dict:
    print("Loading file...")
    event_log = load_xes_file(XES_DATASET_PATH)
    print("File loaded!")
    print("Getting all cases...")
    all_cases = get_all_cases_from_event_log(event_log)
    print("All cases got!")
    print("Getting test cases...")
    test_cases = get_test_cases(all_cases)
    return test_cases


def get_test_cases_under_csv_mode() -> dict:
    print("Loading file...")
    data = load_csv_file(CSV_DATASET_PATH)
    print("File loaded!")
    print("Getting all cases...")
    all_cases = get_all_cases_from_dataframe(data)
    print("All cases got!")
    print("Getting test cases...")
    test_cases = get_test_cases(all_cases)
    return test_cases


def main():
    print("Starting...")

    if TEST_MODE == 'csv':
        test_cases = get_test_cases_under_csv_mode()
    elif TEST_MODE == 'xes':
        test_cases = get_test_cases_under_xes_mode()
    else:
        print("Invalid test mode!")
        return

    print("Test cases got!")
    print("Writing to json file...")
    write_cases_to_json_file(test_cases, TEST_DATASET_PATH)
    print("Json file written!")
    print("Calling post api for cases...")
    call_post_api_for_cases(test_cases)
    print("Post api called for cases!")
    print("Done!")
    sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
