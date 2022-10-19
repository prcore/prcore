import logging
from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

from blupee.routers import event_log, dashboard

# Enable logging
logger = logging.getLogger(__name__)

# Create the app
app = FastAPI(root_path="/api")
app.include_router(event_log.router)
app.include_router(dashboard.router)


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/")
def read_root():
    return {"Hello": "World"}
