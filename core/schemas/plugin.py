import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class PluginBase(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, str | bool | int | float] = {}


class PluginCreate(PluginBase):
    pass


class Plugin(PluginBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    project_id: int

    class Config:
        orm_mode = True
