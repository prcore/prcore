import logging

from core.functions.plugin.common import plugin_run

from plugins.causallift_treatment_effect.config import basic_info
from plugins.causallift_treatment_effect.handler import callback, processed_messages_clean

# Enable logging
logger = logging.getLogger("prcore")


if __name__ == "__main__":
    plugin_run(basic_info, callback, processed_messages_clean)
