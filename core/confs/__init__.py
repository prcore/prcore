import logging
from core.confs.config import APP_TYPE
from core.confs.path import LOG_PATH, PLUGIN_LOG_PATH

# Enable logging
log_path = f"{PLUGIN_LOG_PATH}/{APP_TYPE}" if APP_TYPE == "plugin" else LOG_PATH
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename=f"{log_path}/log",
    filemode="a"
)
logger = logging.getLogger(__name__)
