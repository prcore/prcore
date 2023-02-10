import logging
import json

from pandas import DataFrame
from sklearn.model_selection import GroupShuffleSplit
from sqlalchemy.orm import Session

import core.models.event_log as event_log_model
import core.schemas.definition as definition_schema
from core.confs import path
from core.crud.event_log import set_datasets_name
from core.enums.definition import ColumnDefinition
from core.functions.definition.util import get_column_definition, get_defined_column_name
from core.functions.event_log.df import get_dataframe
from core.functions.general.etc import process_daemon
from core.functions.general.file import get_new_path
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def start_pre_processing(project_id: int, db: Session, db_event_log: event_log_model.EventLog) -> bool:
    # Start pre-processing the data
    p = process_daemon(func=pre_process_data, args=(db, db_event_log))
    memory.pre_processing_tasks[project_id] = p
    return True


def pre_process_data(db: Session, db_event_log: event_log_model.EventLog) -> bool:
    # Pre-process the data
    result = False

    try:
        # Split dataframe
        df = get_dataframe(db_event_log)
        splitter = GroupShuffleSplit(test_size=.20, n_splits=2, random_state=7)
        split = splitter.split(df, groups=df['Case ID'])
        train_indexes, simulation_indexes = next(split)
        training_df = df.iloc[train_indexes]
        simulation_df = df.iloc[simulation_indexes]

        # Get processed cases data from training
        cases = get_cases(training_df, definition_schema.Definition(**db_event_log.definition.dict()))
        training_cases = cases[:int(len(cases) * 0.8)]

        # Save the data
        training_data_path = get_new_path(base_path=f"{path.EVENT_LOG_TRAINING_DATA_PATH}/", suffix=".json")
        simulation_df_path = get_new_path(base_path=f"{path.EVENT_LOG_SIMULATION_DF_PATH}/", suffix=".pkl")

        with open(training_data_path, "w") as f:
            json.dump(training_cases, f, ensure_ascii=False)

        simulation_df.to_pickle(simulation_df_path)

        # Update the database
        set_datasets_name(db, db_event_log, training_data_path, simulation_df_path)
        result = True
    except Exception as e:
        logger.warning(f"Pre-processing failed: {e}", exc_info=True)

    return result


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
            events.append(event)
        cases[case_identifier] = events

    return cases
