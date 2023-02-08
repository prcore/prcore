import logging

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core import glovar

# Enable logging
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = (f"postgresql+psycopg://{glovar.POSTGRES_USER}:{glovar.POSTGRES_PASSWORD}"
                           f"@{glovar.DB_HOST}:{glovar.DB_PORT}/{glovar.POSTGRES_DB}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db(request: Request):
    return request.state.db
