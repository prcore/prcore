import logging

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core import confs

# Enable logging
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = (f"postgresql+psycopg://{confs.POSTGRES_USER}:{confs.POSTGRES_PASSWORD}"
                           f"@{confs.DB_HOST}:{confs.DB_PORT}/{confs.POSTGRES_DB}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db(request: Request):
    return request.state.db
