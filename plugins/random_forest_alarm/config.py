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
    "name": "Random forest negative outcome probability",
    "prescription_type": PluginType.ALARM,
    "description": "This plugin predicts the alarm probability based on the random forest algorithm.",
    "parameters": {}
}
needed_columns: List[ColumnDefinition] = [ColumnDefinition.OUTCOME]
