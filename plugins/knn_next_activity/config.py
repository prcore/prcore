import logging

from core.confs import config
from core.enums.plugin import PluginType

# Enable logging
logger = logging.getLogger(__name__)

# Pre-defined configuration
basic_info = {
    "id": config.APP_ID,
    "name": "KNN next activity prediction",
    "prescription_type": PluginType.NEXT_ACTIVITY,
    "description": "This plugin predicts the next activity based on the KNN algorithm.",
    "parameters": {
        "n_neighbors": 3
    }
}
