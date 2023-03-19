import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import core.schemas.response.event as event_response
from core.functions.common.request import get_real_ip, get_db
from core.security.token import validate_token
from core.services.event import process_new_event

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event")


@router.post("/{project_id}", response_model=event_response.PostEventResponse)
async def receive_event(request: Request, project_id: int, db: Session = Depends(get_db),
                        _: bool = Depends(validate_token)):
    logger.warning(f"Receive event for project {project_id} - from IP {get_real_ip(request)}")
    request_body = await request.json()
    return process_new_event(request_body, project_id, db)
