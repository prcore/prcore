import logging

from core.functions.common.timer import processed_messages_clean

from plugins.common.starter import plugin_scheduler, plugin_run
from plugins.knn_next_activity import memory
from plugins.knn_next_activity.config import basic_info
from plugins.knn_next_activity.handler import callback

# Enable logging
logger = logging.getLogger(__name__)
for _ in logging.root.manager.loggerDict:
    if _.startswith("pika"):
        logging.getLogger(_).setLevel(logging.CRITICAL)


if __name__ == "__main__":
    plugin_scheduler(processed_messages_clean, memory.processed_messages)
    plugin_run(basic_info, callback)
