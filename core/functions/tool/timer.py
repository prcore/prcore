import logging
from datetime import datetime

import core.crud.project as project_crud
from core.enums.status import ProjectStatus
from core.starters import memory
from core.functions.project.simulation import stop_simulation
from core.starters.database import SessionLocal

# Enable logging
logger = logging.getLogger(__name__)


def stop_unread_simulations() -> bool:
    # Stop unread simulations
    result = False

    try:
        datetime_now = datetime.now()
        for project_id in list(memory.simulation_projects.keys()):
            project_datetime = memory.simulation_projects.get(project_id)
            if not project_datetime:
                continue
            if (datetime_now - project_datetime).total_seconds() > 5 * 60:
                with SessionLocal() as db:
                    db_project = project_crud.get_project_by_id(db, project_id)
                    if not db_project:
                        continue
                    if db_project.status != ProjectStatus.SIMULATING:
                        continue
                    stop_simulation(db, db_project)
    except Exception as e:
        logger.warning(f"Stop unread simulations error: {e}", exc_info=True)

    return result
