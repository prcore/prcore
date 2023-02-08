import os

from tomli import load

from core.confs.path import CONFIG_PATH

# Load the config
with open(CONFIG_PATH, mode="rb") as fp:
    config = load(fp)
    token = config["core"]["security"]["token"]
    username = config["core"]["security"]["username"]
    password = config["core"]["security"]["password"]

# Load the environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
POSTGRES_DB = os.environ.get('POSTGRES_DB')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

if any(env is None for env in (DB_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)):
    raise ValueError("Missing environment variables")
