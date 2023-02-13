import logging
from time import sleep

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.orm import close_all_sessions
from sqlalchemy.exc import OperationalError
from tzlocal import get_localzone

from core import security
from core.starters.database import Base, engine, SessionLocal
from core.starters.rabbitmq import parameters
from core.functions.general.etc import thread
from core.functions.message.handler import callback, start_consuming, stop_consuming, consuming_stopped
from core.functions.message.sender import send_online_inquires
from core.functions.tool.timers import log_rotation, processed_messages_clean
from core.routers import event, event_log, plugin, project

# Enable logging
logger = logging.getLogger(__name__)

# Create all tables
while True:
    try:
        Base.metadata.create_all(bind=engine)
        break
    except OperationalError:
        print("Database is not ready. Trying again in 5 seconds...")
        sleep(5)
print("Database is connected")

# Create the app
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(event.router)
app.include_router(event_log.router)
app.include_router(plugin.router)
app.include_router(project.router)
app.include_router(security.router)


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


@app.get("/")
def read_root():
    return {
        "API": "https://prcore.chaos.run",
        "Documentation": "https://prcore-docs.chaos.run",
        "Swagger UI": "https://prcore.chaos.run/docs",
        "RabbitMQ Management": "https://prcore-rabbitmq.chaos.run"
    }


@app.on_event("shutdown")
def shutdown_event():
    # Close the database session
    close_all_sessions()

    # Close the rabbitmq connection
    stop_consuming.set()

    # Wait for the rabbitmq connection to close
    while not consuming_stopped.is_set():
        sleep(0.5)


# Start a scheduler
scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": 300}, timezone=str(get_localzone()))
scheduler.add_job(log_rotation, "cron", hour=23, minute=59)
scheduler.add_job(send_online_inquires, "interval", minutes=5)
scheduler.add_job(processed_messages_clean, "interval", minutes=5)
scheduler.start()

# Start a thread to consume messages
thread(start_consuming, (parameters, "core", callback, 1))

# Send online inquires
send_online_inquires()
