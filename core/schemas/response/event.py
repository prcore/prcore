import logging

from pydantic import BaseModel

from core.schemas.event import Event

# Enable logging
logger = logging.getLogger(__name__)


class PostEventResponse(BaseModel):
    message: str
    event: Event
