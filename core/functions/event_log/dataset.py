import logging
import json

from pandas import DataFrame
from sqlalchemy.orm import Session

import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
from core import glovar, confs
from core.crud.event_log import set_datasets_name
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_column_definition, get_defined_column_name
from core.functions.event_log.df import get_dataframe
from core.functions.general.etc import process_daemon
from core.functions.general.file import get_new_path

# Enable logging
logger = logging.getLogger(__name__)


def start_pre_processing(project_id: int, db: Session, db_event_log: event_log_model.EventLog) -> bool:
    # Start pre-processing the data
    p = process_daemon(func=pre_process_data, args=(db, db_event_log))
    glovar.pre_processing_tasks[project_id] = p
    return True


def pre_process_data(db: Session, db_event_log: event_log_model.EventLog) -> bool:
    # Pre-process the data
    df = get_dataframe(db_event_log)
    cases = get_cases(df, definition_schema.Definition(**db_event_log.definition.dict()))
    training_cases = cases[:int(len(cases) * 0.8)]
    test_cases = cases[int(len(cases) * 0.8):]
    training_data_path = get_new_path(base_path=f"{confs.EVENT_LOG_TRAINING_DATA_PATH}/", suffix=".json")
    simulation_df_path = get_new_path(base_path=f"{confs.EVENT_LOG_SIMULATION_DF_PATH}/", suffix=".pkl")

    with open(training_data_path, "w") as f:
        json.dump(training_cases, f, ensure_ascii=False)

    with open(simulation_df_path, "w") as f:
        json.dump(test_cases, f, ensure_ascii=False)

    set_datasets_name(db, db_event_log, training_data_path, simulation_df_path)
    return True


def get_cases(df: DataFrame, definition: definition_schema.Definition) -> dict[str, list[dict]]:
    cases = {}
    columns = df.columns.tolist()
    special_definitions = {ColumnDefinition.ACTIVITY, ColumnDefinition.TIMESTAMP,
                           ColumnDefinition.TRANSITION, ColumnDefinition.START_TIMESTAMP,
                           ColumnDefinition.END_TIMESTAMP, ColumnDefinition.RESOURCE, ColumnDefinition.DURATION,
                           ColumnDefinition.COST}
    case_id_column_name = get_defined_column_name(definition.columns_definition, ColumnDefinition.CASE_ID)

    for case_id, events_df in df.groupby(case_id_column_name):
        case_identifier = str(case_id)
        events = []
        for _, row in events_df.iterrows():
            event = {}
            for column in columns:
                if get_column_definition(column, definition.columns_definition) == ColumnDefinition.CASE_ID:
                    continue
                if get_column_definition(column, definition.columns_definition) in special_definitions:
                    event[get_column_definition(column, definition.columns_definition).value] = row[column]
                else:
                    event[column] = row[column]
            events.append(event)
        cases[case_identifier] = events

    return cases

