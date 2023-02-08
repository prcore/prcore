import logging

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base

# Enable logging
logger = logging.getLogger(__name__)


class Plugin(Base):
    __tablename__ = "plugin"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    parameters = Column(JSONB, nullable=False, default={})
    project_id = Column(Integer, ForeignKey("project.id"))

    project = relationship("Project", back_populates="plugins")
