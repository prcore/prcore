from typing import List

from core.functions.event_log.csv import process_csv_file
from core.models.case import Case

CSV_PATH = ("/home/zhaosi/Documents/SE/4/Thesis/Application/backend/data/datasets"
            "/prepared_treatment_outcome_bpic2012.csv")


def get_cases() -> List[Case]:
    # get cases from the csv file
    return process_csv_file(CSV_PATH, "test").cases
