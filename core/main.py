import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from core.database import Base, engine, SessionLocal
from core.routers import event_log, project

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
    except Exception as e:
        logger.error(e)
    finally:
        request.state.db.close()
    return response

app.include_router(event_log.router)
app.include_router(project.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
