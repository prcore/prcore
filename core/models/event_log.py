import logging

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.starters import memory
from core.starters.database import Base

# Enable logging
logger = logging.getLogger(__name__)


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    file_name = Column(String, nullable=False)
    saved_name = Column(String, unique=True, nullable=False)
    df_name = Column(String, unique=True, nullable=True)
    training_df_name = Column(String, unique=True, nullable=True)
    simulation_df_name = Column(String, unique=True, nullable=True)
    definition_id = Column(Integer, ForeignKey("definition.id"))

    definition = relationship("Definition")
