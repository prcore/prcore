import logging
from os import mkdir
from os.path import exists
from core.confs.config import APP_ID
from core.confs.path import CORE_LOG_PATH, PLUGIN_LOG_PATH, PROCESSOR_LOG_PATH

# Enable logging
if config.APP_ID == "core":
    log_path = CORE_LOG_PATH
elif config.APP_ID == "processor":
    log_path = PROCESSOR_LOG_PATH
else:
    log_path = PLUGIN_LOG_PATH

mkdir(log_path) if not exists(log_path) else None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename=f"{log_path}/log",
    filemode="a"
)
logger = logging.getLogger(__name__)
