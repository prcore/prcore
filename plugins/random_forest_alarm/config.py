import logging
from typing import Any, Dict

from core.confs import config
from core.enums.dataset import EncodingType
from core.enums.definition import ColumnDefinition
from core.enums.plugin import PluginType

# Enable logging
logger = logging.getLogger(__name__)

# Pre-defined configuration
basic_info: Dict[str, Any] = {
    "id": config.APP_ID,
    "name": "Random forest negative outcome probability",
    "prescription_type": PluginType.ALARM,
    "description": "This plugin predicts the alarm probability based on the random forest algorithm.",
    "parameters": {
        "encoding": EncodingType.SIMPLE_INDEX
    },
    "needed_columns": [ColumnDefinition.OUTCOME],
    "needed_info_for_training": [],
    "needed_info_for_prediction": [],
    "supported_encoding": [EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED, EncodingType.SIMPLE_INDEX]
}
