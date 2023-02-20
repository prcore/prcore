import logging

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from core.starters.database import Base
from core.enums.definition import Transition

# Enable logging
logger = logging.getLogger(__name__)


class Definition(Base):
    __tablename__ = "definition"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    columns_definition = Column(JSONB, nullable=False)
    outcome_definition = Column(JSONB)
    treatment_definition = Column(JSONB)
    fast_mode = Column(Boolean, default=True)
    start_transition = Column(String, default=Transition.START)
    complete_transition = Column(String, default=Transition.COMPLETE)
