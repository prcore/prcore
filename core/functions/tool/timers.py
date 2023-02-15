import logging
from datetime import datetime

from core.starters import memory

# Enable logging
logger = logging.getLogger("prcore")


def processed_messages_clean() -> bool:
    # Clean processed messages
    result = False

    try:
        datetime_now = datetime.now()
        for message_id in list(memory.processed_messages.keys()):
            message_datetime = memory.processed_messages.get(message_id)
            if not message_datetime or (datetime_now - message_datetime).total_seconds() > 15 * 60:
                memory.processed_messages.pop(message_id)
        result = True
    except Exception as e:
        logger.warning(f"Processed messages clean error: {e}", exc_info=True)

    return result
