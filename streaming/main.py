import json
import requests
from time import sleep

from pm4py import read_xes


ID_OFFSET = 80000
ALL_DATASET_PATH = "../data/datasets/OrderFullfilment.xes"
TEST_DATASET_PATH = "../data/datasets/test_cases.json"
THE_SPLIT = 0.8
DASHBOARD_ID = 4781


def load_xes_file(path):
    event_log = read_xes(path)

    if not event_log:
        print("File not valid")

    return event_log


def get_all_cases(event_log):
    cases = {}

    for i in range(len(event_log)):
        case_id = ID_OFFSET + i
        cases[case_id] = get_all_events(case_id, event_log[i])

    return cases


def get_all_events(case_id, case):
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
    for i in range(int(len(cases) * THE_SPLIT), len(cases)):
        test_cases[i + ID_OFFSET] = cases[i + ID_OFFSET]
    return test_cases


def write_cases_to_json_file(cases: dict, path: str):
    # Write to json file with indent 4
    with open(path, "w") as file:
        json.dump(cases, file, indent=4)


def call_post_api_for_cases(cases: dict):
    for case_id in cases:
        case = cases[case_id]
        # Check if the event is the last one
        for i in range(len(case)):
            event = case[i]
            event["dashboard_id"] = DASHBOARD_ID
            event.pop("attributes")
            event["status"] = "closed" if i == len(case) - 1 else "ongoing"
            print(f"Sending the event: {json.dumps(event, indent=4)}")
            requests.post("http://localhost:8000/event", json=event)
            print("Event sent!")
            sleep(3)


def main():
    print("Starting...")
    print("Loading file...")
    event_log = load_xes_file(ALL_DATASET_PATH)
    print("File loaded!")
    print("Getting all cases...")
    all_cases = get_all_cases(event_log)
    print("All cases got!")
    print("Getting test cases...")
    test_cases = get_test_cases(all_cases)
    print("Test cases got!")
    print("Writing to json file...")
    write_cases_to_json_file(test_cases, TEST_DATASET_PATH)
    print("Json file written!")
    print("Calling post api for cases...")
    call_post_api_for_cases(test_cases)
    print("Post api called for cases!")
    print("Done!")
    sleep(5)


if __name__ == "__main__":
    main()
