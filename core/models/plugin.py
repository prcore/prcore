import logging

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.starters.database import Base

# Enable logging
logger = logging.getLogger(__name__)


class Plugin(Base):
    __tablename__ = "plugin"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    project_id = Column(Integer, ForeignKey("project.id"))
    key = Column(String, nullable=False)
    prescription_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    parameters = Column(JSONB, nullable=False, default={})
    additional_info = Column(JSONB, nullable=False, default={})
    status = Column(String, nullable=True)
    error = Column(String, nullable=True)
    disabled = Column(Boolean, nullable=True, default=False)
    model_name = Column(String, nullable=True)

    project = relationship("Project", back_populates="plugins")
