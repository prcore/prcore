import logging
from time import sleep
from urllib.parse import quote

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.confs import config

# Enable logging
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = (f"postgresql+psycopg://{config.POSTGRES_USER}:{quote(config.POSTGRES_PASSWORD)}"
                           f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}")

engine = create_engine(
    url=SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def retry_crud(func: callable, max_retires: int, *args, **kwargs):
    for i in range(max_retires):
        try:
            with SessionLocal() as db:
                return func(db, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Retrying crud {func.__name__} in 1 second... ({i + 1}/{max_retires})")
            sleep(1)
            if i == max_retires - 1:
                raise e
