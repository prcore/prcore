import logging

from fastapi import Request

# Enable logging
logger = logging.getLogger(__name__)


def get_real_ip(request: Request) -> str:
    # Get the real ip address of the client
    result = ""

    try:
        result = request.headers.get("X-Forwarded-For")

        if not result:
            return request.client.host

        if "," not in result:
            return result

        result = result.split(",")[0]
    except Exception as e:
        logger.warning(f"Get real ip error: {e}", exc_info=True)

    return result
