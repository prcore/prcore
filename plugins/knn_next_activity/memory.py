import logging

# Enable logging
logger = logging.getLogger(__name__)

# Data stored in memory
instances: dict[int, any] = {}
