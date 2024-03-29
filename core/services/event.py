import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Any

import core.crud.case as case_crud
import core.crud.event as event_crud
import core.crud.project as project_crud
import core.schemas.case as case_schema
import core.schemas.definition as definition_schema
import core.schemas.event as event_schema
from core.enums.definition import ColumnDefinition
from core.enums.error import ErrorType
from core.enums.status import PluginStatus
from core.functions.definition.util import get_defined_column_name
from core.functions.event.job import prepare_prefix_and_send
from core.functions.event.validation import validate_columns
from core.functions.plugin.util import enhance_additional_infos, get_active_plugins
from core.functions.project.streaming import check_simulation
from core.starters import memory

# Enable logging
logger = logging.getLogger(__name__)


def process_new_event(request_body: Any, project_id: int, db: Session) -> dict:
    # Get project from the database
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_FOUND)

    # Check if the project is streaming
    streaming_project = memory.streaming_projects.get(db_project.id)
    if not streaming_project or streaming_project["finished"].is_set():
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_STREAMING)

    # Get columns definition from the database
    db_definition = db_project.event_log.definition
    columns_definition = db_definition.columns_definition
    case_attributes = db_definition.case_attributes

    # Check if request body has all the columns previously defined
    validate_columns(request_body, columns_definition, case_attributes)

    # Check if there is already a case with the same case ID
    case_id = str(request_body[get_defined_column_name(columns_definition, ColumnDefinition.CASE_ID)])
    db_case = case_crud.get_case_by_project_id_and_case_id(db, project_id, case_id)
    if not db_case:
        db_case = case_crud.create_case(db, case_schema.CaseCreate(project_id=project_id, case_id=case_id))

    # Create the event
    db_event = event_crud.create_event(
        db=db,
        event=event_schema.EventCreate(project_id=project_id, attributes=request_body),
        case_id=db_case.id
    )

    # Check if there is a complete indicator
    complete_indicator = get_defined_column_name(columns_definition, ColumnDefinition.COMPLETE_INDICATOR)
    complete_indicator = complete_indicator or ColumnDefinition.COMPLETE_INDICATOR
    if complete_indicator in request_body and request_body[complete_indicator] in ["1", "true", "True", "TRUE", True]:
        case_crud.mark_as_completed(db, db_case)
        db_event = event_crud.mark_as_prescribed(db, db_event)
        check_simulation(db, db_project)
        return {
            "message": "Event received successfully, this is the last event of the case",
            "event": db_event
        }

    # Get additional infos
    additional_infos = enhance_additional_infos(
        additional_infos={plugin.key: plugin.additional_info for plugin in db_project.plugins},
        active_plugins=get_active_plugins(),
        definition=definition_schema.Definition.from_orm(db_definition)
    )

    # Send the event to the plugins
    prepare_prefix_and_send(
        project_id=project_id,
        model_names={plugin.key: plugin.model_name for plugin in db_project.plugins
                     if plugin.status == PluginStatus.STREAMING},
        event_id=db_event.id,
        columns_definition=columns_definition,
        case_attributes=case_attributes,
        data=[db_event.attributes for db_event in db_case.events],
        additional_infos=additional_infos
    )
    return {
        "message": "Event received successfully",
        "event": db_event
    }
