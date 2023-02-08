import logging

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core import confs

# Enable logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/token")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def validate_token(token: str = Depends(oauth2_scheme)) -> bool:
    # Check if the token is valid
    if token == confs.token:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    if username != core.confs.config.username or password != core.confs.config.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": core.confs.config.token, "token_type": "bearer"}
