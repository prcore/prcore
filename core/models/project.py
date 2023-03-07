import logging

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.starters.database import Base

# Enable logging
logger = logging.getLogger(__name__)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=True)
    error = Column(String, nullable=True)
    event_log_id = Column(Integer, ForeignKey("event_log.id"))

    event_log = relationship("EventLog")
    plugins = relationship("Plugin", back_populates="project")
