import logging

from core.functions.plugin.common import plugin_run

from plugins.knn_next_activity.config import basic_info
from plugins.knn_next_activity.handler import callback

# Enable logging
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    plugin_run(basic_info, callback)
