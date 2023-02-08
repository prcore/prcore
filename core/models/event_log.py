import logging

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core import glovar
from core.database import Base

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
    training_data_name = Column(String, unique=True, nullable=True)
    test_data_name = Column(String, unique=True, nullable=True)
    definition_id = Column(Integer, ForeignKey("definition.id"))

    definition = relationship("Definition")


class PreviousEventLog(EventLog):
    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.previous_event_logs)):
                if glovar.previous_event_logs[i].id == self.id:
                    glovar.previous_event_logs[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.previous_event_logs.append(self)


class CurrentEventLog(EventLog):
    def save(self):
        with glovar.save_lock:
            already_saved = False
            for i in range(len(glovar.current_event_logs)):
                if glovar.current_event_logs[i].id == self.id:
                    glovar.current_event_logs[i] = self
                    already_saved = True
                    break
            not already_saved and glovar.current_event_logs.append(self)
