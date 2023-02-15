import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger("prcore")


class PluginBase(BaseModel):
    name: str
    prescription_type: str
    description: str | None = None
    parameters: dict[str, str | bool | int | float | list] = {}
    status: str | None = None


class PluginCreate(PluginBase):
    key: str
    model_name: str | None = None


class Plugin(PluginBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True
