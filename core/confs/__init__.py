import logging
from os import mkdir
from os.path import exists
from core.confs.config import APP_ID
from core.confs.path import CORE_LOG_PATH, PLUGIN_LOG_PATH

# Enable logging
log_path = CORE_LOG_PATH if config.APP_ID == "core" else f"{PLUGIN_LOG_PATH}/{APP_ID}"
mkdir(log_path) if not exists(log_path) else None
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename=f"{log_path}/log",
    filemode="a"
)
logger = logging.getLogger("prcore")
