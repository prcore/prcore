import logging
from tzlocal import get_localzone

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from core import security
from core.database import Base, engine, SessionLocal
from core.functions.tool.timers import log_rotation
from core.routers import event_log, plugin, project

# Enable logging
logger = logging.getLogger(__name__)

# Create all tables
Base.metadata.create_all(bind=engine)

# Create the app
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    except ValidationError as e:
        logger.warning(e, exc_info=True)
        response = Response(e.json(), status_code=400)
    except Exception as e:
        logger.warning(e, exc_info=True)
    finally:
        request.state.db.close()
    return response

app.include_router(event_log.router)
app.include_router(plugin.router)
app.include_router(project.router)
app.include_router(security.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 300}, timezone=str(get_localzone()))
scheduler.add_job(log_rotation, "cron", hour=23, minute=59)
scheduler.start()
