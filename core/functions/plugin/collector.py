import logging

# Enable logging
logger = logging.getLogger(__name__)


def get_online_plugins() -> list[str]:
    # Get all online plugins
    return [
        "plugin_knn_next_activity",
        "plugin_random_forest_alarm",
        "plugin_casual_lift_treatment_effect"
    ]
