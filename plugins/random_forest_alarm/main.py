import logging

from core.functions.plugin.common import plugin_run, plugin_scheduler

from plugins.random_forest_alarm.config import basic_info
from plugins.random_forest_alarm.handler import callback, processed_messages_clean

# Enable logging
logger = logging.getLogger(__name__)
for _ in logging.root.manager.loggerDict:
    if _.startswith("pika"):
        logging.getLogger(_).setLevel(logging.CRITICAL)


if __name__ == "__main__":
    plugin_scheduler(processed_messages_clean)
    plugin_run(basic_info, callback)
