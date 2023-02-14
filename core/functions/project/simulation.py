import logging
import multiprocessing

from sqlalchemy.orm import Session

import core.crud.plugin as plugin_crud
import core.crud.project as project_crud
import core.models.project as project_model
import core.schemas.definition as definition_schema
from core.enums.status import PluginStatus, ProjectStatus
from core.functions.general.etc import process_daemon
from core.functions.message.sender import send_streaming_stop_to_all_plugins
from core.starters import memory
from simulation import run_simulation

# Enable logging
logger = logging.getLogger(__name__)


def proceed_simulation(simulation_df_name: str, project_id: int, definition: definition_schema.Definition) -> bool:
    # Proceed simulation
    if memory.simulation_events.get(project_id) is None:
        end_event = multiprocessing.Event()
    else:
        end_event = memory.simulation_events[project_id]
        end_event.clear()
    memory.simulation_events[project_id] = end_event
    process_daemon(run_simulation, (simulation_df_name, end_event, project_id, definition))
    return True


def check_simulation(db: Session, db_project: project_model.Project) -> bool:
    # Check if the simulation is finished
    end_event = memory.simulation_events.get(db_project.id)
    if not end_event or end_event.is_set():
        stop_simulation(db, db_project)
    return True


def stop_simulation(db: Session, db_project: project_model.Project, redefined: bool = False) -> bool:
    # Stop the simulation
    new_project_status = ProjectStatus.WAITING if redefined else ProjectStatus.TRAINED
    db_project = project_crud.update_status(db, db_project, new_project_status)
    for plugin in db_project.plugins:
        if redefined:
            plugin_crud.update_status(db, plugin, PluginStatus.WAITING)
        elif plugin.status == PluginStatus.STREAMING:
            plugin_crud.update_status(db, plugin, PluginStatus.TRAINED)
    end_event = memory.simulation_events.get(db_project.id)
    end_event and end_event.set()
    send_streaming_stop_to_all_plugins(db_project.id, [plugin.key for plugin in db_project.plugins])
    return True
