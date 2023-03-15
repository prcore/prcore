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
    "name": "CasualLift resource allocation",
    "prescription_type": PluginType.RESOURCE_ALLOCATION,
    "description": "This plugin uses Uplift Modeling package CasualLift to get resource allocation base on CATE",
    "parameters": {
        "encoding": EncodingType.SIMPLE_INDEX
    },
    "needed_columns": [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT],
    "needed_info_for_training": [],
    "needed_info_for_prediction": ["available_resources", "treatment_duration"],
    "supported_encoding": [EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED, EncodingType.SIMPLE_INDEX]
}
