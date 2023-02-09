import os

# Load the environment variables
API_TOKEN = os.environ.get('API_TOKEN')
API_USERNAME = os.environ.get('API_USERNAME')
API_PASSWORD = os.environ.get('API_PASSWORD')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT')
POSTGRES_DB = os.environ.get('POSTGRES_DB')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

# Check if all environment variables are set
all_envs = {API_TOKEN, API_USERNAME, API_PASSWORD,
            POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD}
if any(env is None for env in all_envs):
    raise ValueError("Missing environment variables")
