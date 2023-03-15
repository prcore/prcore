import logging

from plugins.common.starter import plugin_scheduler, plugin_run
from plugins.causallift_resource_allocation.algorithm import CausalLiftAlgorithm
from plugins.causallift_resource_allocation.config import basic_info

# Enable logging
logger = logging.getLogger(__name__)
for _ in logging.root.manager.loggerDict:
    if _.startswith("pika"):
        logging.getLogger(_).setLevel(logging.CRITICAL)
    if _.startswith("causallift"):
        logging.getLogger(_).setLevel(logging.CRITICAL)

if __name__ == "__main__":
    plugin_scheduler(basic_info)
    plugin_run(CausalLiftAlgorithm, basic_info)
