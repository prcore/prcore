import logging
from datetime import datetime
from typing import Dict

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
