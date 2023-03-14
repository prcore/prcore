import logging
from typing import Any

from pydantic import BaseModel

from core.schemas.plugin import Plugin

# Enable logging
logger = logging.getLogger(__name__)


class AllPluginsResponse(BaseModel):
    message: str
    plugins: list[Plugin] = []


class PluginResponse(BaseModel):
    message: str
    plugin: Plugin


class AvailablePluginsResponse(BaseModel):
    message: str
    plugins: dict[str, dict[str, Any]] = {}
