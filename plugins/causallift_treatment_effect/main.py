import logging

from core.functions.common.plugin import plugin_scheduler, plugin_run
from core.functions.common.timer import processed_messages_clean

from plugins.causallift_treatment_effect import memory
from plugins.causallift_treatment_effect.config import basic_info
from plugins.causallift_treatment_effect.handler import callback

# Enable logging
logger = logging.getLogger(__name__)
for _ in logging.root.manager.loggerDict:
    if _.startswith("pika"):
        logging.getLogger(_).setLevel(logging.CRITICAL)


if __name__ == "__main__":
    plugin_scheduler(processed_messages_clean, memory.processed_messages)
    plugin_run(basic_info, callback)
