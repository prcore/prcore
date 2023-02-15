import logging

from core.functions.plugin.common import plugin_run

from plugins.knn_next_activity.config import basic_info
from plugins.knn_next_activity.handler import callback, processed_messages_clean

# Enable logging
logger = logging.getLogger("prcore")


if __name__ == "__main__":
    plugin_run(basic_info, callback, processed_messages_clean)
