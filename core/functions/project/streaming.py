import asyncio
import logging
import json
from datetime import datetime
from multiprocessing import Event as ProcessEvent
from multiprocessing.synchronize import Event as ProcessEventType

from fastapi import Request
from sqlalchemy.orm import Session

import core.crud.event as event_crud
from core.crud import project as project_crud, plugin as plugin_crud
from core.enums.definition import ColumnDefinition
from core.enums.status import ProjectStatus, PluginStatus
from core.functions.general.etc import process_daemon
from core.functions.message.sender import send_streaming_stop_to_all_plugins
from core.functions.plugin.collector import get_active_plugins
from core.models import project as project_model
from core.schemas import definition as definition_schema
from core.starters import memory
from core.starters.database import engine
from simulation import run_simulation

# Enable logging
logger = logging.getLogger(__name__)


async def event_generator(request: Request, db: Session, project_id: int):
    try:
        yield {
            "event": "notification",
            "id": 0,
            "data": "CONNECTED"
        }
        i = 1
        while True:
            if await request.is_disconnected():
                break
            if memory.streaming_projects[project_id]["finished"].is_set():
                yield {
                    "event": "notification",
                    "id": i,
                    "data": "FINISHED"
                }
                break
            data = get_data(db, project_id)
            if data:
                yield {
                    "event": "message",
                    "id": i,
                    "data": json.dumps(data)
                }
                i += 1
                event_ids = [event["id"] for event in data]
                mark_as_sent(db, event_ids)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.warning(f"Steam result reading connection of project {project_id} is closed")
        memory.streaming_projects[project_id]["read_time"] = datetime.now()
        memory.streaming_projects[project_id]["reading"] = False
    except Exception as e:
        logger.error(f"Error in the SSE stream: {e}", exc_info=True)
        yield {
            "event": "error",
            "data": f"Error in the SSE stream: {e}"
        }


def get_data(db: Session, project_id: int) -> list[dict]:
    # Get data of the SSE stream
    result = []

    try:
        db_events = event_crud.get_events_prescribed_but_not_sent_by_project_id(db, project_id)
        result = [
            {
                "id": event.id,
                "timestamp": event.updated_at.isoformat(),
                "case_completed": event.case.completed,
                "data": {key: value for key, value in event.attributes.items()
                         if key != ColumnDefinition.COMPLETE_INDICATOR},
                "prescriptions": event.prescriptions
            }
            for event in db_events
        ]
    except Exception as e:
        logger.error(f"Error getting data of the SSE stream: {e}")

    return result


def get_finished_event(project_id: int, streaming_type: str) -> ProcessEventType:
    if memory.streaming_projects.get(project_id) is None:
        result = ProcessEvent()
        memory.streaming_projects[project_id] = {
            "type": streaming_type,
            "finished": result,
            "start_time": datetime.now(),
            "read_time": None,
            "reading": False
        }
    else:
        result = memory.streaming_projects[project_id]["finished"]
        result.clear()
        memory.streaming_projects[project_id]["type"] = streaming_type
        memory.streaming_projects[project_id]["start_time"] = datetime.now()
        memory.streaming_projects[project_id]["read_time"] = None
    return result


def mark_as_sent(db: Session, event_ids: list[int]) -> bool:
    # Mark an event as sent
    result = False

    try:
        event_crud.mark_as_sent_by_event_ids(db, event_ids)
    except Exception as e:
        logger.error(f"Error marking an event as sent: {e}")

    return result


def enable_streaming(db: Session, project_id: int) -> None:
    # Enable the streaming
    db_project = project_crud.get_project_by_id(db, project_id)
    if not get_active_plugins() or any([plugin.status != PluginStatus.STREAMING for plugin in db_project.plugins]):
        return
    if db_project.status == ProjectStatus.SIMULATING:
        proceed_simulation(
            simulation_df_name=db_project.event_log.simulation_df_name,
            project_id=db_project.id,
            definition=db_project.event_log.definition
        )
    elif db_project.status == ProjectStatus.STREAMING:
        get_finished_event(db_project.id, "streaming")


def disable_streaming(db: Session, db_project: project_model.Project, redefined: bool = False) -> bool:
    # Disable the streaming
    new_project_status = ProjectStatus.WAITING if redefined else ProjectStatus.TRAINED
    db_project = project_crud.update_status(db, db_project, new_project_status)
    for plugin in db_project.plugins:
        if redefined:
            plugin_crud.update_status(db, plugin, PluginStatus.WAITING)
        elif plugin.status == PluginStatus.STREAMING:
            plugin_crud.update_status(db, plugin, PluginStatus.TRAINED)
    if memory.streaming_projects.get(db_project.id):
        memory.streaming_projects[db_project.id]["finished"].set()
    send_streaming_stop_to_all_plugins(db_project.id, [plugin.key for plugin in db_project.plugins])
    return True


def check_simulation(db: Session, db_project: project_model.Project) -> None:
    # Check if the simulation is finished
    if db_project.status != ProjectStatus.SIMULATING:
        return
    streaming_project = memory.streaming_projects.get(db_project.id)
    if (not streaming_project
            or (streaming_project["type"] == "simulation"
                and streaming_project["finished"].is_set())):
        disable_streaming(db, db_project)


def proceed_simulation(simulation_df_name: str, project_id: int, definition: definition_schema.Definition) -> bool:
    # Proceed simulation
    finished = get_finished_event(project_id, "simulation")
    engine.dispose()
    process_daemon(run_simulation, (simulation_df_name, finished, project_id, definition))
    return True
