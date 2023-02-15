import logging
from typing import Any, Dict, List

from core.confs import config
from core.enums.definition import ColumnDefinition
from core.enums.plugin import PluginType

# Enable logging
logger = logging.getLogger("prcore")

# Pre-defined configuration
basic_info: Dict[str, Any] = {
    "id": config.APP_ID,
    "name": "KNN next activity prediction",
    "prescription_type": PluginType.NEXT_ACTIVITY,
    "description": "This plugin predicts the next activity based on the KNN algorithm.",
    "parameters": {
        "n_neighbors": 3
    }
}
needed_columns: List[ColumnDefinition] = []
