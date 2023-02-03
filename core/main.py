import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.routers import event_log

# Enable logging
logger = logging.getLogger(__name__)

# Create the app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(event_log.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
