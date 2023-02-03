import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core import glovar

# Enable logging
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def validate_token(token: str = Depends(oauth2_scheme)) -> bool:
    # Check if the token is valid
    if token == glovar.token:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )
