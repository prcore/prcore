import logging
from typing import Any, Dict, List

from core.confs import config
from core.enums.dataset import EncodingType
from core.enums.definition import ColumnDefinition
from core.enums.plugin import PluginType

# Enable logging
logger = logging.getLogger(__name__)

# Pre-defined configuration
basic_info: Dict[str, Any] = {
    "id": config.APP_ID,
    "name": "KNN next activity prediction",
    "prescription_type": PluginType.NEXT_ACTIVITY,
    "description": "This plugin predicts the next activity based on the KNN algorithm.",
    "parameters": {
        "encoding": EncodingType.SIMPLE_INDEX,
        "n_neighbors": 3,
    },
    "needed_columns": [],
    "needed_info_for_training": [],
    "needed_info_for_prediction": [],
    "supported_encoding": [EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED, EncodingType.SIMPLE_INDEX]
}
needed_columns: List[ColumnDefinition] = []
