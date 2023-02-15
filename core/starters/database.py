import logging
from urllib.parse import quote

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.confs import config

# Enable logging
logger = logging.getLogger("prcore")

SQLALCHEMY_DATABASE_URL = (f"postgresql+psycopg://{config.POSTGRES_USER}:{quote(config.POSTGRES_PASSWORD)}"
                           f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
