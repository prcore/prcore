import logging
from datetime import datetime

from pydantic import BaseModel

# Enable logging
logger = logging.getLogger(__name__)


class PluginBase(BaseModel):
    pass


class PluginCreate(PluginBase):
    key: str
    prescription_type: str
    name: str
    description: str | None = None
    parameters: dict[str, str | bool | int | float | list] = {}
    additional_info: dict[str, str | bool | int | float | list] = {}
    status: str | None = None


class PluginUpdate(PluginBase):
    disabled: bool = False


class Plugin(PluginBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    key: str
    prescription_type: str
    name: str
    description: str | None = None
    parameters: dict[str, str | bool | int | float | list] = {}
    additional_info: dict[str, str | bool | int | float | list] = {}
    status: str | None = None
    error: str | None = None
    disabled: bool = False

    class Config:
        orm_mode = True
