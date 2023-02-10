import os

# Load the environment variables
APP_ID = os.environ.get("APP_ID")
API_TOKEN = os.environ.get("API_TOKEN")
API_USERNAME = os.environ.get("API_USERNAME")
API_PASSWORD = os.environ.get("API_PASSWORD")
ENABLED_PLUGINS = os.environ.get("ENABLED_PLUGINS")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_DB = os.environ.get("POSTGRES_DB")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS")

# Check if all environment variables are set
if APP_ID is None:
    raise ValueError("Missing environment variable APP_ID")

if APP_ID == "core":
    all_envs = {API_TOKEN, API_USERNAME, API_PASSWORD,
                ENABLED_PLUGINS,
                POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
                RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS}
elif APP_ID == "test":
    all_envs = set()
else:
    all_envs = {RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS}

if any(env is None for env in all_envs):
    raise ValueError("Missing environment variables")
