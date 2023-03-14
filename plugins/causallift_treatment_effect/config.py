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
    "name": "CasualLift treatment effect",
    "prescription_type": PluginType.TREATMENT_EFFECT,
    "description": ("This plugin uses Uplift Modeling package CasualLift to get the CATE "
                    "and probability of outcome if treatment is applied or not"),
    "parameters": {
        "encoding": EncodingType.SIMPLE_INDEX
    },
    "needed_columns": [ColumnDefinition.OUTCOME, ColumnDefinition.TREATMENT],
    "needed_info_for_training": [],
    "needed_info_for_prediction": ["treatment_definition"],
    "supported_encoding": [EncodingType.BOOLEAN, EncodingType.FREQUENCY_BASED, EncodingType.SIMPLE_INDEX]
}
