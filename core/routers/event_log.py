import logging

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from sqlalchemy.orm import Session

import core.schemas.request.event_log as event_log_request
import core.schemas.response.event_log as event_log_response
from core.functions.common.request import get_real_ip, get_db
from core.security.token import validate_token
from core.services.event_log import (process_uploaded_event_log, process_event_log_definition,
                                     process_re_uploaded_event_log, process_event_logs_reading,
                                     process_event_log_definition_reading, process_event_log_reading)

# Enable logging
logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/event_log")


@router.post("", response_model=event_log_response.UploadEventLogResponse)
def upload_event_log(request: Request, file: UploadFile = Form(), separator: str = Form(","),
                     test: UploadFile = Form(None),
                     db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Upload event log <{file and file.filename}> - from IP {get_real_ip(request)}")
    return process_uploaded_event_log(file, separator, test, db)


@router.put("/{event_log_id}", response_model=event_log_response.UpdateEventLogResponse)
def update_event_log(request: Request, event_log_id: int, update_body: event_log_request.ColumnsDefinitionRequest,
                     db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Update event log {event_log_id} - from IP {get_real_ip(request)}")
    return process_event_log_definition(event_log_id, update_body, db)


@router.put("/{event_log_id}/upload", response_model=event_log_response.UpdateEventLogResponse)
def re_upload_event_log(request: Request, event_log_id: int, file: UploadFile = Form(), separator: str = Form(","),
                        db: Session = Depends(get_db), _: bool = Depends(validate_token)):
    logger.warning(f"Re-upload event log <{file and file.filename}> to {event_log_id} - "
                   f"from IP {get_real_ip(request)}")
    return process_re_uploaded_event_log(event_log_id, file, separator, db)


@router.get("/all", response_model=event_log_response.AllEventLogsResponse)
def read_event_logs(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                    _: bool = Depends(validate_token)):
    logger.warning(f"Read event logs - from IP {get_real_ip(request)}")
    return process_event_logs_reading(skip, limit, db)


@router.get("/{event_log_id}/definition", response_model=event_log_response.EventLogDefinitionResponse)
def read_event_log_definition(request: Request, event_log_id: int, db: Session = Depends(get_db),
                              _: bool = Depends(validate_token)):
    logger.warning(f"Read event log definition for {event_log_id} - from IP {get_real_ip(request)}")
    return process_event_log_definition_reading(event_log_id, db)


@router.get("/{event_log_id}", response_model=event_log_response.EventLogResponse)
def read_event_log(request: Request, event_log_id: int, db: Session = Depends(get_db),
                   _: bool = Depends(validate_token)):
    logger.warning(f"Read event log {event_log_id} - from IP {get_real_ip(request)}")
    return process_event_log_reading(event_log_id, db)
