import logging

from core.functions.plugin.common import plugin_run

from plugins.causallift_treatment_effect.config import basic_info
from plugins.causallift_treatment_effect.handler import callback, processed_messages_clean

# Enable logging
logger = logging.getLogger(__name__)
for _ in logging.root.manager.loggerDict:
    if _.startswith("pika"):
        logging.getLogger(_).setLevel(logging.CRITICAL)


if __name__ == "__main__":
    plugin_run(basic_info, callback, processed_messages_clean)
