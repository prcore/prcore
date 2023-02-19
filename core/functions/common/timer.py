import logging
from datetime import datetime
from subprocess import run
from typing import Dict

from core import confs
from core.functions.general.etc import get_readable_time
from core.functions.general.file import move_file

# Enable logging
logger = logging.getLogger(__name__)


def processed_messages_clean(processed_messages: Dict[str, datetime]) -> bool:
    # Clean processed messages
    result = False

    try:
        datetime_now = datetime.now()
        for message_id in list(processed_messages.keys()):
            message_datetime = processed_messages.get(message_id)
            if not message_datetime or (datetime_now - message_datetime).total_seconds() > 15 * 60:
                processed_messages.pop(message_id)
        result = True
    except Exception as e:
        logger.warning(f"Processed messages clean error: {e}", exc_info=True)

    return result


def log_rotation() -> bool:
    # Log rotation
    result = False

    try:
        move_file(f"{confs.log_path}/log", f"{confs.log_path}/log-{get_readable_time(the_format='%Y%m%d')}")

        with open(f"{confs.log_path}/log", "w", encoding="utf-8") as f:
            f.write("")

        # Reconfigure the logger
        [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.WARNING,
            filename=f"{confs.log_path}/log",
            filemode="a"
        )

        run(f"find {confs.log_path}/log-* -mtime +30 -delete", shell=True)

        result = True
    except Exception as e:
        logger.warning(f"Log rotation error: {e}", exc_info=True)

    return result
