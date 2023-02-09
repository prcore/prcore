import logging
from multiprocessing import Process

from pandas import DataFrame

# Enable logging
logger = logging.getLogger(__name__)

# Data in memory
dataframes: dict[int, DataFrame] = {}
pre_processing_tasks: dict[int, Process] = {}
available_plugins: dict[str, dict[str, str]] = {
    "plugin_knn_next_activity": {
        "name": "KNN Next Activity",
        "prescription_type": "NEXT_ACTIVITY",
        "description": "Predict the next activity using KNN algorithm",
        "parameters": {
            "n_neighbors": 3
        },
        "online": True
    },
    "plugin_random_forest_alarm": {
        "name": "Random Forest Alarm",
        "prescription_type": "ALARM",
        "description": "Predict the probability of alarm using Random Forest algorithm",
        "parameters": {},
        "online": True
    },
    "plugin_casual_lift_treatment_effect": {
        "name": "CasualLift Treatment Effect",
        "prescription_type": "TREATMENT_EFFECT",
        "description": "Predict the treatment effect using CasualLift algorithm",
        "parameters": {},
        "online": True
    }
}
