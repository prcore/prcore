import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core import glovar

# Enable logging
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = (f"postgresql+psycopg://{glovar.POSTGRES_USER}:{glovar.POSTGRES_PASSWORD}"
                           f"@localhost:{glovar.DB_PORT}/{glovar.POSTGRES_DB}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
