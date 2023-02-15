import logging

from pydantic import BaseModel

from core.schemas.plugin import Plugin

# Enable logging
logger = logging.getLogger("prcore")


class AllPluginsResponse(BaseModel):
    message: str
    plugins: list[Plugin] = []
