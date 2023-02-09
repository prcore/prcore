import os

from tomli import load

from core.confs.path import CONFIG_PATH

# Load the config
with open(CONFIG_PATH, mode="rb") as fp:
    config = load(fp)
    API_TOKEN = config["core"]["security"]["token"]
    API_USERNAME = config["core"]["security"]["username"]
    API_PASSWORD = config["core"]["security"]["password"]

# Load the environment variables
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
POSTGRES_DB = os.environ.get('POSTGRES_DB')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

if any(env is None for env in (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)):
    raise ValueError("Missing environment variables")
