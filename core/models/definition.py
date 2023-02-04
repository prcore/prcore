import logging
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from core.database import Base

# Enable logging
logger = logging.getLogger(__name__)


class Definition(Base):
    __tablename__ = "definition"

    id: int = Column(Integer, primary_key=True, index=True)
    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: datetime = Column(DateTime(timezone=True), onupdate=func.now())
