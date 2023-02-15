from pathlib import Path

# Path variables
EVENT_LOG_DATAFRAME_PATH = "data/event_logs/dataframe"
EVENT_LOG_TRAINING_DF_PATH = "data/event_logs/training_df"
EVENT_LOG_SIMULATION_DF_PATH = "data/event_logs/simulation_df"
EVENT_LOG_RAW_PATH = "data/event_logs/raw"
PLUGIN_LOG_PATH = "data/plugins/logs"
PLUGIN_MODEL_PATH = "data/plugins/models"
CORE_LOG_PATH = "data/logs"
TEMP_PATH = "data/tmp"

# Allowed extensions
ALLOWED_EXTENSIONS = ["xes", "csv", "zip"]
ALLOWED_EXTRACTED_EXTENSIONS = ["xes", "csv"]

# Create directories
all_paths = [EVENT_LOG_DATAFRAME_PATH, EVENT_LOG_TRAINING_DF_PATH, EVENT_LOG_SIMULATION_DF_PATH, EVENT_LOG_RAW_PATH,
             PLUGIN_LOG_PATH, PLUGIN_MODEL_PATH,
             CORE_LOG_PATH,
             TEMP_PATH]
for path in all_paths:
    Path(path).mkdir(parents=True, exist_ok=True)
