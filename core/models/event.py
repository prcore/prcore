import logging

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.starters.database import Base

# Enable logging
logger = logging.getLogger("prcore")


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    project_id = Column(Integer, ForeignKey("project.id"))
    attributes = Column(JSONB, nullable=False, default={})
    prescriptions = Column(JSONB, nullable=False, default={})
    prescribed = Column(Boolean, nullable=False, default=False)
    sent = Column(Boolean, nullable=False, default=False)
    case_id = Column(Integer, ForeignKey("case.id"))

    case = relationship("Case", back_populates="events")
