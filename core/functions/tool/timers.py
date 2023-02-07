import logging
from subprocess import run

from core import confs
from core.functions.general.etc import get_readable_time
from core.functions.general.file import move_file

# Enable logging
logger = logging.getLogger(__name__)


def log_rotation() -> bool:
    # Log rotation
    result = False

    try:
        move_file(f"{confs.LOG_PATH}/log", f"{confs.LOG_PATH}/log-{get_readable_time(the_format='%Y%m%d')}")

        with open(f"{confs.LOG_PATH}/log", "w", encoding="utf-8") as f:
            f.write("")

        # Reconfigure the logger
        [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.WARNING,
            filename=f"{confs.LOG_PATH}/log",
            filemode="a"
        )

        run(f"find {confs.LOG_PATH}/log-* -mtime +30 -delete", shell=True)

        result = True
    except Exception as e:
        logger.warning(f"Log rotation error: {e}", exc_info=True)

    return result
