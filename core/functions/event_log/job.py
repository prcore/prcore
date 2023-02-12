import logging

import core.crud.event_log as event_log_crud
import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
import core.schemas.plugin as plugin_schema
from core.enums.status import PluginStatus
from core.functions.event_log.dataset import pre_process_data
from core.functions.message.sender import send_training_data_to_all_plugins
from core.starters.database import SessionLocal

# Enable logging
logger = logging.getLogger(__name__)


def start_pre_processing(project_id: int, event_log_id: int, active_plugins: dict) -> bool:
    # Start pre-processing the data
    with SessionLocal() as db:
        db_event_log = event_log_crud.get_event_log_by_id(db, event_log_id)
        training_df_name = pre_process_data(db, db_event_log)
        if not training_df_name:
            project_crud.set_project_error(db, project_id, "Failed to pre-process the data")
            return False
        plugin_ids = list(active_plugins.keys())
        for plugin_id in plugin_ids:
            plugin_crud.create_plugin(
                db=db,
                plugin=plugin_schema.PluginCreate(
                    name=active_plugins[plugin_id]["name"],
                    prescription_type=active_plugins[plugin_id]["prescription_type"],
                    description=active_plugins[plugin_id]["description"],
                    parameters=active_plugins[plugin_id]["parameters"],
                    status=PluginStatus.WAITING
                ),
                project_id=project_id
            )
        send_training_data_to_all_plugins(project_id, training_df_name, plugin_ids)
    return True
