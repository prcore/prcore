import logging

from plugins.common.starter import plugin_scheduler, plugin_run
from plugins.random_forest_alarm.algorithm import RandomAlgorithm
from plugins.random_forest_alarm.config import basic_info

# Enable logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    plugin_scheduler(basic_info)
    plugin_run(RandomAlgorithm, basic_info)
