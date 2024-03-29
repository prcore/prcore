import logging
from datetime import datetime
from typing import Any

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
    parameters: dict[str, Any] = {}
    additional_info: dict[str, Any] = {}
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
    parameters: dict[str, Any] = {}
    additional_info: dict[str, Any] = {}
    status: str | None = None
    error: str | None = None
    disabled: bool = False

    class Config:
        orm_mode = True
