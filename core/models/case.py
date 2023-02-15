import logging

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.starters.database import Base

# Enable logging
logger = logging.getLogger(__name__)


class Case(Base):
    __tablename__ = "case"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    project_id = Column(Integer, ForeignKey("project.id"))
    case_id = Column(String, nullable=False)
    completed = Column(Boolean, nullable=False, default=False)

    events = relationship("Event", back_populates="case")
