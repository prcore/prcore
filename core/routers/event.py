import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import core.crud.case as case_crud
import core.crud.event as event_crud
import core.crud.project as project_crud
import core.schemas.case as case_schema
import core.schemas.event as event_schema
import core.schemas.response.event as event_response
from core.enums.definition import ColumnDefinition
from core.enums.error import ErrorType
from core.enums.status import ProjectStatus
from core.functions.definition.util import get_defined_column_name
from core.functions.event.job import prepare_prefix_and_send
from core.functions.general.request import get_real_ip, get_db
from core.functions.project.simulation import check_simulation
from core.security.token import validate_token

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event")


@router.post("/{project_id}", response_model=event_response.PostEventResponse)
async def receive_event(request: Request, project_id: int, db: Session = Depends(get_db),
                        _: bool = Depends(validate_token)):
    logger.warning(f"Receive event - from IP {get_real_ip(request)}")
    request_body = await request.json()

    # Get project from the database
    db_project = project_crud.get_project_by_id(db, project_id)
    if not db_project:
        raise HTTPException(status_code=400, detail="No valid project provided")
    if db_project.status not in {ProjectStatus.STREAMING, ProjectStatus.SIMULATING}:
        raise HTTPException(status_code=400, detail=ErrorType.PROJECT_NOT_STREAMING)

    # Get columns definition from the database
    db_definition = db_project.event_log.definition
    columns_definition = db_definition.columns_definition
    case_attributes = db_definition.case_attributes

    # Check if request body has all the columns previously defined
    for column in columns_definition:
        if column not in request_body:
            raise HTTPException(status_code=400, detail=f"Missing pre-defined column {column.name}")
    if case_attributes:
        for column in case_attributes:
            if column not in request_body:
                raise HTTPException(status_code=400, detail=f"Missing case attribute {column.name}")

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

    # Send the event to the plugins
    prepare_prefix_and_send(
        project_id=project_id,
        model_names={plugin.key: plugin.model_name for plugin in db_project.plugins},
        event_id=db_event.id,
        columns_definition=columns_definition,
        case_attributes=case_attributes,
        data=[db_event.attributes for db_event in db_case.events]
    )
    return {
        "message": "Event received successfully",
        "event": db_event
    }
