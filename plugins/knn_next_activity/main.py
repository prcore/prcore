import logging

from plugins.common.starter import plugin_scheduler, plugin_run
from plugins.knn_next_activity.algorithm import KNNAlgorithm
from plugins.knn_next_activity.config import basic_info

# Enable logging
logger = logging.getLogger(__name__)
for _ in logging.root.manager.loggerDict:
    if _.startswith("pika"):
        logging.getLogger(_).setLevel(logging.CRITICAL)

if __name__ == "__main__":
    plugin_scheduler(basic_info)
    plugin_run(KNNAlgorithm, basic_info)
